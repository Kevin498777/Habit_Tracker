# routes/pages.py — Blueprint de páginas estáticas/legales
from datetime import datetime

from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html', current_date=datetime.now())


@pages_bp.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_conditions.html', current_date=datetime.now())


@pages_bp.route('/contact')
def contact():
    return render_template('contact.html', current_date=datetime.now())