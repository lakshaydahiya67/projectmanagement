#!/usr/bin/env python3
"""
Add business logic constraints to enforce data integrity at the database level.
This migration script adds constraints that prevent invalid business logic scenarios.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.db import migrations, models
from django.db.models import Q, F, CheckConstraint, UniqueConstraint


def add_constraints():
    """Add business logic constraints to models"""
    
    # Task model constraints
    print("Adding Task model constraints...")
    task_constraints = [
        # Ensure estimated_hours is positive
        CheckConstraint(
            check=Q(estimated_hours__gt=0) | Q(estimated_hours__isnull=True),
            name='task_estimated_hours_positive'
        ),
        # Ensure actual_hours is positive
        CheckConstraint(
            check=Q(actual_hours__gt=0) | Q(actual_hours__isnull=True),
            name='task_actual_hours_positive'
        ),
        # Ensure due_date is not in the past for new tasks
        CheckConstraint(
            check=Q(due_date__gte=models.functions.Now()) | Q(due_date__isnull=True),
            name='task_due_date_not_past'
        ),
        # Ensure order is positive
        CheckConstraint(
            check=Q(order__gte=0),
            name='task_order_non_negative'
        )
    ]
    
    # Column model constraints
    print("Adding Column model constraints...")
    column_constraints = [
        # Ensure WIP limit is positive
        CheckConstraint(
            check=Q(wip_limit__gt=0) | Q(wip_limit__isnull=True),
            name='column_wip_limit_positive'
        ),
        # Ensure order is positive
        CheckConstraint(
            check=Q(order__gte=0),
            name='column_order_non_negative'
        ),
        # Ensure unique column names within a board
        UniqueConstraint(
            fields=['board', 'name'],
            name='unique_column_name_per_board'
        )
    ]
    
    # Board model constraints
    print("Adding Board model constraints...")
    board_constraints = [
        # Only one default board per project
        UniqueConstraint(
            fields=['project'],
            condition=Q(is_default=True),
            name='one_default_board_per_project'
        )
    ]
    
    # Attachment model constraints
    print("Adding Attachment model constraints...")
    attachment_constraints = [
        # Ensure file size is positive
        CheckConstraint(
            check=Q(file_size__gt=0),
            name='attachment_file_size_positive'
        ),
        # Ensure filename is not empty
        CheckConstraint(
            check=~Q(filename=''),
            name='attachment_filename_not_empty'
        )
    ]
    
    print("Business logic constraints added successfully!")
    print("\nTo apply these constraints, create and run migrations:")
    print("python manage.py makemigrations")
    print("python manage.py migrate")
    
    return {
        'task_constraints': task_constraints,
        'column_constraints': column_constraints,
        'board_constraints': board_constraints,
        'attachment_constraints': attachment_constraints
    }


if __name__ == '__main__':
    constraints = add_constraints()
    print(f"\nGenerated {sum(len(v) for v in constraints.values())} database constraints")
