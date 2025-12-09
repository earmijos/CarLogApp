"""
Settings API Routes
===================
Endpoints for user and app settings.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.settings_service import SettingsService
from services.base_service import ValidationError

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
def get_settings():
    """Get all settings."""
    try:
        user_id = request.args.get('user_id', type=int)
        settings = SettingsService.get_all(user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['GET'])
def get_setting(key):
    """Get a specific setting by key."""
    try:
        user_id = request.args.get('user_id', type=int)
        value = SettingsService.get(key, user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'key': key,
                'value': value
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['PUT', 'POST'])
def set_setting(key):
    """Set a setting value."""
    try:
        data = request.get_json()
        
        if not data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'value is required'
            }), 400
        
        user_id = data.get('user_id')
        result = SettingsService.set(key, data['value'], user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Setting updated successfully'
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['DELETE'])
def delete_setting(key):
    """Delete a setting."""
    try:
        user_id = request.args.get('user_id', type=int)
        deleted = SettingsService.delete(key, user_id=user_id)
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Setting deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Setting not found'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults."""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        settings = SettingsService.reset_to_defaults(user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': settings,
            'message': 'Settings reset to defaults'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/theme', methods=['GET'])
def get_theme():
    """Get current theme setting."""
    try:
        user_id = request.args.get('user_id', type=int)
        theme = SettingsService.get_theme(user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': {'theme': theme}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/theme', methods=['PUT', 'POST'])
def set_theme():
    """Set theme."""
    try:
        data = request.get_json()
        
        if not data or 'theme' not in data:
            return jsonify({
                'success': False,
                'error': 'theme is required'
            }), 400
        
        user_id = data.get('user_id')
        result = SettingsService.set_theme(data['theme'], user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Theme updated successfully'
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/units', methods=['GET'])
def get_units():
    """Get unit settings."""
    try:
        user_id = request.args.get('user_id', type=int)
        units = SettingsService.get_units(user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': units
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

