"""
Analytics Service
=================
Provides analytics and calculations for vehicle data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query
from services.base_service import validate_vin, ValidationError


class AnalyticsService:
    """Service for analytics calculations."""
    
    @classmethod
    def get_vehicle_dashboard(cls, vin: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a vehicle."""
        vin = validate_vin(vin)
        
        # Get vehicle info
        vehicle = execute_query(
            "SELECT * FROM vehicles WHERE vin = ?",
            (vin,), fetch_one=True
        )
        
        if not vehicle:
            return {'error': 'Vehicle not found'}
        
        # Get repair stats
        repair_stats = execute_query("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(cost), 0) as total_cost,
                MAX(date) as last_repair_date
            FROM repairs WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        # Get fuel stats
        fuel_stats = execute_query("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(gallons), 0) as total_gallons,
                MIN(odometer) as first_odometer,
                MAX(odometer) as last_odometer
            FROM fuel_logs WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        # Get trip stats
        trip_stats = execute_query("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(distance), 0) as total_miles,
                SUM(CASE WHEN is_business = 1 THEN distance ELSE 0 END) as business_miles
            FROM trips WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        # Calculate MPG
        mpg_data = cls.calculate_mpg(vin)
        
        # Get upcoming maintenance
        upcoming_maintenance = execute_query("""
            SELECT service_type, next_due_mileage
            FROM maintenance_intervals 
            WHERE vin = ? AND next_due_mileage IS NOT NULL
            ORDER BY next_due_mileage ASC
            LIMIT 3
        """, (vin,))
        
        # Get overdue maintenance
        current_mileage = vehicle['current_mileage'] or 0
        overdue = execute_query("""
            SELECT service_type, next_due_mileage
            FROM maintenance_intervals 
            WHERE vin = ? AND next_due_mileage < ?
        """, (vin, current_mileage))
        
        return {
            'vehicle': dict(vehicle),
            'current_mileage': current_mileage,
            'repairs': {
                'count': repair_stats['count'],
                'total_cost': round(repair_stats['total_cost'], 2),
                'last_repair_date': repair_stats['last_repair_date']
            },
            'fuel': {
                'fill_ups': fuel_stats['count'],
                'total_cost': round(fuel_stats['total_cost'], 2),
                'total_gallons': round(fuel_stats['total_gallons'], 2)
            },
            'trips': {
                'count': trip_stats['count'],
                'total_miles': round(trip_stats['total_miles'], 1),
                'business_miles': round(trip_stats['business_miles'] or 0, 1)
            },
            'mpg': mpg_data,
            'upcoming_maintenance': [dict(m) for m in upcoming_maintenance],
            'overdue_maintenance': [dict(m) for m in overdue],
            'total_cost': round(
                repair_stats['total_cost'] + fuel_stats['total_cost'], 2
            )
        }
    
    @classmethod
    def calculate_mpg(cls, vin: str) -> Dict[str, Any]:
        """Calculate MPG statistics for a vehicle."""
        vin = validate_vin(vin)
        
        logs = execute_query("""
            SELECT gallons, odometer
            FROM fuel_logs 
            WHERE vin = ? AND full_tank = 1
            ORDER BY odometer DESC
            LIMIT 11
        """, (vin,))
        
        if len(logs) < 2:
            return {
                'average_mpg': None,
                'last_mpg': None,
                'data_points': 0
            }
        
        mpg_values = []
        for i in range(len(logs) - 1):
            miles = logs[i]['odometer'] - logs[i + 1]['odometer']
            gallons = logs[i]['gallons']
            if gallons > 0 and miles > 0:
                mpg_values.append(miles / gallons)
        
        if not mpg_values:
            return {
                'average_mpg': None,
                'last_mpg': None,
                'data_points': 0
            }
        
        return {
            'average_mpg': round(sum(mpg_values) / len(mpg_values), 1),
            'last_mpg': round(mpg_values[0], 1),
            'best_mpg': round(max(mpg_values), 1),
            'worst_mpg': round(min(mpg_values), 1),
            'data_points': len(mpg_values)
        }
    
    @classmethod
    def calculate_cost_per_mile(cls, vin: str) -> Dict[str, Any]:
        """Calculate cost per mile for a vehicle."""
        vin = validate_vin(vin)
        
        # Get total costs
        costs = execute_query("""
            SELECT 
                (SELECT COALESCE(SUM(cost), 0) FROM repairs WHERE vin = ?) as repair_cost,
                (SELECT COALESCE(SUM(total_cost), 0) FROM fuel_logs WHERE vin = ?) as fuel_cost
        """, (vin, vin), fetch_one=True)
        
        # Get mileage range
        mileage = execute_query("""
            SELECT MIN(odometer) as first, MAX(odometer) as last
            FROM fuel_logs WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        total_cost = costs['repair_cost'] + costs['fuel_cost']
        total_miles = (mileage['last'] or 0) - (mileage['first'] or 0)
        
        if total_miles <= 0:
            # Try using mileage history
            mileage = execute_query("""
                SELECT MIN(mileage) as first, MAX(mileage) as last
                FROM mileage_history WHERE vin = ?
            """, (vin,), fetch_one=True)
            total_miles = (mileage['last'] or 0) - (mileage['first'] or 0)
        
        cost_per_mile = total_cost / total_miles if total_miles > 0 else 0
        
        return {
            'total_cost': round(total_cost, 2),
            'repair_cost': round(costs['repair_cost'], 2),
            'fuel_cost': round(costs['fuel_cost'], 2),
            'total_miles': total_miles,
            'cost_per_mile': round(cost_per_mile, 3),
            'fuel_cost_per_mile': round(
                costs['fuel_cost'] / total_miles if total_miles > 0 else 0, 3
            ),
            'repair_cost_per_mile': round(
                costs['repair_cost'] / total_miles if total_miles > 0 else 0, 3
            )
        }
    
    @classmethod
    def get_monthly_spending(
        cls, 
        vin: str, 
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get monthly spending breakdown."""
        vin = validate_vin(vin)
        
        # Get repair spending by month
        repairs = execute_query("""
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(cost) as amount
            FROM repairs 
            WHERE vin = ? AND date >= date('now', ?)
            GROUP BY strftime('%Y-%m', date)
        """, (vin, f'-{months} months'))
        
        # Get fuel spending by month
        fuel = execute_query("""
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(total_cost) as amount
            FROM fuel_logs 
            WHERE vin = ? AND date >= date('now', ?)
            GROUP BY strftime('%Y-%m', date)
        """, (vin, f'-{months} months'))
        
        # Combine into monthly totals
        monthly = {}
        for r in repairs:
            month = r['month']
            if month not in monthly:
                monthly[month] = {'month': month, 'repairs': 0, 'fuel': 0}
            monthly[month]['repairs'] = round(r['amount'], 2)
        
        for f in fuel:
            month = f['month']
            if month not in monthly:
                monthly[month] = {'month': month, 'repairs': 0, 'fuel': 0}
            monthly[month]['fuel'] = round(f['amount'], 2)
        
        # Calculate totals
        result = []
        for month in sorted(monthly.keys()):
            data = monthly[month]
            data['total'] = round(data['repairs'] + data['fuel'], 2)
            result.append(data)
        
        return result
    
    @classmethod
    def get_spending_by_category(cls, vin: str) -> List[Dict[str, Any]]:
        """Get spending breakdown by repair category."""
        vin = validate_vin(vin)
        
        query = """
            SELECT 
                service as category,
                COUNT(*) as count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM repairs 
            WHERE vin = ?
            GROUP BY service
            ORDER BY total_cost DESC
        """
        results = execute_query(query, (vin,))
        
        return [
            {
                'category': r['category'],
                'count': r['count'],
                'total_cost': round(r['total_cost'], 2),
                'avg_cost': round(r['avg_cost'], 2)
            }
            for r in results
        ]
    
    @classmethod
    def get_fuel_price_trend(cls, vin: str, months: int = 6) -> List[Dict[str, Any]]:
        """Get fuel price trend over time."""
        vin = validate_vin(vin)
        
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                AVG(price_per_gallon) as avg_price,
                MIN(price_per_gallon) as min_price,
                MAX(price_per_gallon) as max_price,
                SUM(gallons) as total_gallons,
                SUM(total_cost) as total_cost
            FROM fuel_logs 
            WHERE vin = ? AND date >= date('now', ?)
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month ASC
        """
        results = execute_query(query, (vin, f'-{months} months'))
        
        return [
            {
                'month': r['month'],
                'avg_price': round(r['avg_price'], 3),
                'min_price': round(r['min_price'], 3),
                'max_price': round(r['max_price'], 3),
                'total_gallons': round(r['total_gallons'], 2),
                'total_cost': round(r['total_cost'], 2)
            }
            for r in results
        ]
    
    @classmethod
    def get_all_vehicles_summary(cls) -> List[Dict[str, Any]]:
        """Get summary for all vehicles."""
        query = """
            SELECT 
                v.vin,
                v.year,
                v.make,
                v.model,
                v.current_mileage,
                COALESCE((SELECT SUM(cost) FROM repairs WHERE vin = v.vin), 0) as repair_cost,
                COALESCE((SELECT SUM(total_cost) FROM fuel_logs WHERE vin = v.vin), 0) as fuel_cost,
                COALESCE((SELECT COUNT(*) FROM repairs WHERE vin = v.vin), 0) as repair_count
            FROM vehicles v
            ORDER BY v.make, v.model
        """
        results = execute_query(query)
        
        return [
            {
                'vin': r['vin'],
                'year': r['year'],
                'make': r['make'],
                'model': r['model'],
                'display_name': f"{r['year']} {r['make']} {r['model']}",
                'current_mileage': r['current_mileage'],
                'repair_cost': round(r['repair_cost'], 2),
                'fuel_cost': round(r['fuel_cost'], 2),
                'total_cost': round(r['repair_cost'] + r['fuel_cost'], 2),
                'repair_count': r['repair_count']
            }
            for r in results
        ]

