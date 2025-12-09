"""
Analytics API Routes
====================
Endpoints for analytics and reporting.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.analytics_service import AnalyticsService
from services.base_service import ValidationError

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard/<vin>', methods=['GET'])
def get_dashboard(vin):
    """Get comprehensive dashboard data for a vehicle."""
    try:
        dashboard = AnalyticsService.get_vehicle_dashboard(vin)
        
        if 'error' in dashboard:
            return jsonify({
                'success': False,
                'error': dashboard['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': dashboard
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/mpg/<vin>', methods=['GET'])
def get_mpg(vin):
    """Get MPG statistics for a vehicle."""
    try:
        mpg_data = AnalyticsService.calculate_mpg(vin)
        
        return jsonify({
            'success': True,
            'data': mpg_data
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/cost-per-mile/<vin>', methods=['GET'])
def get_cost_per_mile(vin):
    """Get cost per mile statistics for a vehicle."""
    try:
        cpm_data = AnalyticsService.calculate_cost_per_mile(vin)
        
        return jsonify({
            'success': True,
            'data': cpm_data
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/spending/<vin>', methods=['GET'])
def get_monthly_spending(vin):
    """Get monthly spending breakdown for a vehicle."""
    try:
        months = request.args.get('months', 12, type=int)
        spending = AnalyticsService.get_monthly_spending(vin, months=months)
        
        return jsonify({
            'success': True,
            'data': spending
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/spending-by-category/<vin>', methods=['GET'])
def get_spending_by_category(vin):
    """Get spending breakdown by repair category."""
    try:
        categories = AnalyticsService.get_spending_by_category(vin)
        
        return jsonify({
            'success': True,
            'data': categories
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/fuel-prices/<vin>', methods=['GET'])
def get_fuel_price_trend(vin):
    """Get fuel price trend for a vehicle."""
    try:
        months = request.args.get('months', 6, type=int)
        trend = AnalyticsService.get_fuel_price_trend(vin, months=months)
        
        return jsonify({
            'success': True,
            'data': trend
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/summary', methods=['GET'])
def get_all_vehicles_summary():
    """Get summary for all vehicles."""
    try:
        summary = AnalyticsService.get_all_vehicles_summary()
        
        return jsonify({
            'success': True,
            'data': summary,
            'count': len(summary)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

