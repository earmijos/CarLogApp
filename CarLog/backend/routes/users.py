"""
Users API Routes
================
Endpoints for user management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.user_service import UserService
from services.base_service import ValidationError, NotFoundError

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
def get_users():
    """Get all users."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        users = UserService.get_all(limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'data': users,
            'count': len(users)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a single user by ID."""
    try:
        user = UserService.get_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/default', methods=['GET'])
def get_default_user():
    """Get or create the default user."""
    try:
        user = UserService.get_default_user()
        
        return jsonify({
            'success': True,
            'data': user
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('', methods=['POST'])
def create_user():
    """Create a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user = UserService.create(data)
        
        return jsonify({
            'success': True,
            'data': user,
            'message': 'User created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
def update_user(user_id):
    """Update a user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user = UserService.update(user_id, data)
        
        return jsonify({
            'success': True,
            'data': user,
            'message': 'User updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    try:
        UserService.delete(user_id)
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/<int:user_id>/vehicles', methods=['GET'])
def get_user_vehicles(user_id):
    """Get all vehicles for a user."""
    try:
        vehicles = UserService.get_user_vehicles(user_id)
        
        return jsonify({
            'success': True,
            'data': vehicles,
            'count': len(vehicles)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@users_bp.route('/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get statistics for a user."""
    try:
        stats = UserService.get_user_stats(user_id)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

