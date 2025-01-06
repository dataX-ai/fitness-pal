from django.utils import timezone
from django.db.models import Count, Q, F, Case, When, Value
from ..models import WorkoutSession, Exercise, WhatsAppUser, DashboardDetails
from ..services.logger_service import get_logger
from ..ai_services.nlp_processor import extract_workout_details
from django.db import transaction
from ..dao.exercise_dao import WorkoutSessionDAO
from ..dao.user_dao import UserDAO
from ..dao.dashboard_dao import DashboardDAO
from ..utils.conversion import calculate_goal_weight
import pandas as pd
import numpy as np
import os
from ..utils.config import EXERCISE_LIST_DF

logger = get_logger(__name__)

exercise_metrics = {}
for _, row in EXERCISE_LIST_DF.iterrows():
    exercise_name = row['Exercise Name']
    avg_rep = row['Avg Rep']
    avg_break = row['Avg Break']
    exercise_metrics[exercise_name] = [avg_rep, avg_break]

def process_workout_metrics():
    """Process workout metrics and calculate goal weights for users"""
    try:
        logger.info("Starting to process workout metrics")
        # Get workout stats for all users as a DataFrame
        user_workout_df = WorkoutSessionDAO.get_user_workout_stats()
        if user_workout_df.empty:
            logger.info("No workout data found to process")
            return

        user_workout_df['avg_week_duration'] = (
            user_workout_df['all_time_duration'] / 
            ((user_workout_df['distinct_workout_days'] // 7) + 1)
        ).fillna(0)

        # Get weight history with height and goal type
        user_weight_history = UserDAO.get_users_weight_history()

        if user_weight_history.empty:
            logger.info("No weight history data found to process")
            return

        user_weight_history['calculated_goal_weight'] = user_weight_history.apply(
            lambda row: calculate_goal_weight(row['user_height'], row['user_goal']),
            axis=1
        )

        # Merge workout stats with weight history
        user_workout_df = user_workout_df.merge(
            user_weight_history[[
                'user_id', 'first_weight', 'last_weight', 
                'user_height', 'user_goal', 'calculated_goal_weight'
            ]], 
            on='user_id',
            how='outer'
        )
        
        if user_workout_df.empty:
            logger.info("No data after merging workout and weight history")
            return
            
        logger.info(f"Successfully merged data for {len(user_workout_df)} users")

        # Get existing dashboard records
        existing_dashboards = {
            d.user_id: d for d in DashboardDetails.objects.all()
        }

        records_to_update = []
        records_to_create = []
        
        for _, row in user_workout_df.iterrows():
            user_id = row['user_id']
            if pd.isna(user_id):
                continue
            
            dashboard_data = {
                'all_time_duration': row['all_time_duration'],
                'last_week_duration': row['last_week_duration'],
                'avg_week_duration': row['avg_week_duration'],
                'initial_weight': row['first_weight'],
                'current_weight': row['last_weight'],
                'goal_weight': row['calculated_goal_weight']
            }
            
            # Handle NaN values by converting them to 0
            dashboard_data = {
                k: 0 if pd.isna(v) else v 
                for k, v in dashboard_data.items()
            }
            
            if user_id in existing_dashboards:
                # Update existing record
                dashboard = existing_dashboards[user_id]
                for key, value in dashboard_data.items():
                    setattr(dashboard, key, value)
                records_to_update.append(dashboard)
            else:
                # Create new record
                user = UserDAO.get_user_by_id(user_id)
                if user:
                    dashboard_data['user'] = user
                    records_to_create.append(DashboardDetails(**dashboard_data))

        with transaction.atomic():
            # Use DashboardDAO for bulk operations
            DashboardDAO.bulk_update_dashboard_details(records_to_update)
            DashboardDAO.bulk_create_dashboard_details(records_to_create)

            total_processed = len(records_to_create) + len(records_to_update)
            logger.info(f"Processed and saved workout metrics for {total_processed} users")

    except Exception as e:
        logger.error(f"Error processing workout metrics: {str(e)}")
        return pd.DataFrame()

