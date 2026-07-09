from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request, send_file
from functools import wraps
import json
from io import BytesIO
from datetime import datetime

from models import (
    get_all_elections, get_active_elections, get_election_by_id,
    create_election, close_election, get_candidates_by_election,
    add_candidate, has_user_voted, record_vote, get_vote_results,
    get_all_voters, get_all_votes_with_details
)
from blockchain import Blockchain

# Initialize Blockchain Instance
blockchain = Blockchain()

routes_bp = Blueprint('routes', __name__)

# ==========================================
# AUTH DECORATORS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Unauthorized. Please login."}), 401
            return redirect(url_for('routes.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Access denied. Admin required."}), 403
            return redirect(url_for('routes.login_page'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# HTML VIEW ROUTES
# ==========================================

@routes_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard_page'))
    return redirect(url_for('routes.login_page'))

@routes_bp.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard_page'))
    return render_template('login.html')

@routes_bp.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard_page'))
    return render_template('register.html')

@routes_bp.route('/dashboard')
@login_required
def dashboard_page():
    if session.get('role') == 'admin':
        return redirect(url_for('routes.admin_dashboard'))
    return redirect(url_for('routes.voter_dashboard'))

@routes_bp.route('/voter')
@login_required
def voter_dashboard():
    if session.get('role') != 'voter':
        return redirect(url_for('routes.dashboard_page'))
    return render_template('voter_dashboard.html', user=session)

@routes_bp.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', user=session)


# ==========================================
# API ELECTION ROUTES
# ==========================================

@routes_bp.route('/api/elections', methods=['GET'])
@login_required
def api_get_elections():
    """Retrieves all elections (or only active ones depending on request query)."""
    try:
        active_only = request.args.get('active', 'false').lower() == 'true'
        if active_only:
            elections = get_active_elections()
        else:
            elections = get_all_elections()
        
        # Check if the current user has voted in each election (for UI reference)
        user_id = session.get('user_id')
        role = session.get('role')
        for el in elections:
            el['voted'] = has_user_voted(user_id, el['id']) if role == 'voter' else False
            
        return jsonify({"success": True, "elections": elections}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/elections', methods=['POST'])
@admin_required
def api_create_election():
    """Endpoint for creating elections (Admin only)."""
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    
    if not title:
        return jsonify({"success": False, "message": "Election title is required."}), 400
        
    try:
        election_id = create_election(title, description)
        return jsonify({
            "success": True, 
            "message": "Election created successfully.", 
            "election_id": election_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/elections/<int:election_id>', methods=['GET'])
@login_required
def api_get_election(election_id):
    """Retrieves details of a specific election."""
    try:
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
        
        candidates = get_candidates_by_election(election_id)
        user_id = session.get('user_id')
        role = session.get('role')
        voted = has_user_voted(user_id, election_id) if role == 'voter' else False
        
        return jsonify({
            "success": True, 
            "election": election, 
            "candidates": candidates,
            "has_voted": voted
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/elections/<int:election_id>/close', methods=['POST'])
@admin_required
def api_close_election(election_id):
    """Endpoint to close an election (Admin only)."""
    try:
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
            
        close_election(election_id)
        return jsonify({"success": True, "message": f"Election '{election['title']}' has been closed."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# API CANDIDATE ROUTES
# ==========================================

@routes_bp.route('/api/elections/<int:election_id>/candidates', methods=['POST'])
@admin_required
def api_add_candidate(election_id):
    """Endpoint for adding a candidate to an election (Admin only)."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    party = data.get('party', '').strip()
    details = data.get('details', '').strip()
    
    if not name or not party:
        return jsonify({"success": False, "message": "Candidate name and party are required."}), 400
        
    try:
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
            
        if election['status'] == 'closed':
            return jsonify({"success": False, "message": "Cannot add candidates to a closed election."}), 400
            
        candidate_id = add_candidate(election_id, name, party, details)
        return jsonify({
            "success": True,
            "message": "Candidate added successfully.",
            "candidate_id": candidate_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# API VOTING OPERATION (BLOCKCHAIN INTEGRATED)
# ==========================================

@routes_bp.route('/api/elections/<int:election_id>/vote', methods=['POST'])
@login_required
def api_vote(election_id):
    """Casts a vote. The vote is minted to the custom blockchain ledger."""
    if session.get('role') != 'voter':
        return jsonify({"success": False, "message": "Only registered voters can cast votes."}), 403
        
    data = request.get_json() or {}
    candidate_id = data.get('candidate_id')
    
    if not candidate_id:
        return jsonify({"success": False, "message": "Candidate ID is required."}), 400
        
    user_id = session.get('user_id')
    
    try:
        # 1. Verify election exists and is active
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
            
        if election['status'] == 'closed':
            return jsonify({"success": False, "message": "This election has already closed."}), 400
            
        # 2. Check if user already voted (One Person One Vote prevention)
        if has_user_voted(user_id, election_id):
            return jsonify({"success": False, "message": "You have already casted a vote in this election."}), 400
            
        # 3. Add to blockchain ledger
        block_id, new_block = blockchain.add_vote(user_id, election_id, candidate_id)
        
        # 4. Record to SQL votes tracking table
        record_vote(user_id, election_id, candidate_id, block_id)
        
        return jsonify({
            "success": True,
            "message": "Your vote has been cast and cryptographically secured in the blockchain ledger!",
            "receipt": {
                "block_index": new_block.index,
                "block_hash": new_block.hash,
                "timestamp": new_block.timestamp
            }
        }), 200
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
             return jsonify({"success": False, "message": "Double voting attempt detected and blocked."}), 400
        return jsonify({"success": False, "message": f"Voting transaction failed: {str(e)}"}), 500


# ==========================================
# API RESULTS & ANALYTICS
# ==========================================

@routes_bp.route('/api/elections/<int:election_id>/results', methods=['GET'])
@login_required
def api_get_results(election_id):
    """Retrieves results of an election."""
    try:
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
            
        results = get_vote_results(election_id)
        return jsonify({
            "success": True,
            "election": election,
            "results": results
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/admin/voters', methods=['GET'])
@admin_required
def api_get_all_voters():
    """Retrieves list of all registered voters (Admin only)."""
    try:
        voters = get_all_voters()
        return jsonify({"success": True, "voters": voters}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/admin/votes', methods=['GET'])
@admin_required
def api_get_all_votes():
    """Retrieves detailed history of all votes (Admin only)."""
    try:
        votes = get_all_votes_with_details()
        return jsonify({"success": True, "votes": votes}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# API BLOCKCHAIN EXPLORER & VERIFICATION
# ==========================================

@routes_bp.route('/api/blockchain', methods=['GET'])
@login_required
def api_get_blockchain():
    """Retrieves all blocks from the ledger for the Explorer view."""
    try:
        blockchain.load_from_db()
        chain_dicts = [block.to_dict() for block in blockchain.chain]
        return jsonify({"success": True, "chain": chain_dicts, "length": len(chain_dicts)}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/blockchain/verify', methods=['GET'])
@login_required
def api_verify_blockchain():
    """Validates the blockchain chain integrity."""
    try:
        report = blockchain.is_chain_valid()
        return jsonify({"success": True, "data": report}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@routes_bp.route('/api/blockchain/export', methods=['GET'])
@admin_required
def api_export_blockchain():
    """Exports the full blockchain ledger as a JSON download."""
    try:
        blockchain.load_from_db()
        chain_dicts = [block.to_dict() for block in blockchain.chain]
        
        # Serialize the chain dictionary
        json_data = json.dumps(chain_dicts, indent=4)
        
        # Create bytes stream to send file
        buffer = BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"blockchain_ledger_{datetime.now().strftime('%Y%m%d%H%M%S')}.json",
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# REPORTLAB RESULTS PDF GENERATOR
# ==========================================

@routes_bp.route('/api/elections/<int:election_id>/results/pdf', methods=['GET'])
@login_required
def api_export_results_pdf(election_id):
    """Generates and exports election results as a PDF (ReportLab)."""
    try:
        election = get_election_by_id(election_id)
        if not election:
            return jsonify({"success": False, "message": "Election not found."}), 404
            
        results = get_vote_results(election_id)
        
        # Build PDF
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title Style
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=15
        )
        
        # Heading Style
        sub_style = ParagraphStyle(
            name='SubStyle',
            fontName='Helvetica',
            fontSize=11,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=30
        )
        
        # Normal Text
        normal_style = styles['Normal']
        normal_style.textColor = colors.HexColor('#1E293B')
        
        # Table Header
        th_style = ParagraphStyle(
            name='THStyle',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white
        )
        
        # Document Title
        story.append(Paragraph("ELECTION RESULTS REPORT", title_style))
        story.append(Paragraph(f"Election: {election['title']}", ParagraphStyle('E', parent=title_style, fontSize=16, spaceAfter=5)))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Status: {election['status'].upper()}", sub_style))
        story.append(Spacer(1, 10))
        
        # Results Table Data
        table_data = [[
            Paragraph("Rank", th_style),
            Paragraph("Candidate Name", th_style),
            Paragraph("Party", th_style),
            Paragraph("Votes Casted", th_style)
        ]]
        
        total_votes = sum([r['vote_count'] for r in results])
        
        for rank, r in enumerate(results, start=1):
            table_data.append([
                Paragraph(str(rank), normal_style),
                Paragraph(r['name'], normal_style),
                Paragraph(r['party'], normal_style),
                Paragraph(f"{r['vote_count']} votes", normal_style)
            ])
            
        # Draw Results Table
        t = Table(table_data, colWidths=[1.0*inch, 2.5*inch, 2.0*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        
        story.append(t)
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Total Votes Casted:</b> {total_votes}", normal_style))
        story.append(Spacer(1, 40))
        
        # Crypto Disclaimer
        crypto_style = ParagraphStyle(
            name='CryptoStyle',
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor('#64748B'),
            alignment=1 # Center aligned
        )
        story.append(Paragraph("This election was processed and cryptographically validated via a distributed SHA-256 local ledger.", crypto_style))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"election_{election_id}_results.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
