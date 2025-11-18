#!/usr/bin/env python3
"""
GitHub Actions Workflow Validator and Tester

This script validates all GitHub Actions workflows and provides
a comprehensive report on their structure and configuration.
"""

import yaml
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

class WorkflowValidator:
    def __init__(self, workflow_dir: str = '.github/workflows'):
        self.workflow_dir = Path(workflow_dir)
        self.errors = []
        self.warnings = []
        self.workflows = {}

    def validate_all(self) -> bool:
        """Validate all workflow files"""
        print("🔍 Validating GitHub Actions Workflows\n")
        print("=" * 70)

        if not self.workflow_dir.exists():
            print(f"❌ Workflow directory not found: {self.workflow_dir}")
            return False

        workflow_files = list(self.workflow_dir.glob('*.yml')) + \
                        list(self.workflow_dir.glob('*.yaml'))

        if not workflow_files:
            print(f"❌ No workflow files found in {self.workflow_dir}")
            return False

        print(f"Found {len(workflow_files)} workflow files\n")

        for filepath in sorted(workflow_files):
            self._validate_workflow(filepath)

        self._print_summary()
        return len(self.errors) == 0

    def _validate_workflow(self, filepath: Path):
        """Validate a single workflow file"""
        filename = filepath.name
        print(f"\n📄 {filename}")
        print("-" * 70)

        try:
            with open(filepath, 'r') as f:
                content = yaml.safe_load(f)

            if content is None:
                self.errors.append(f"{filename}: Empty workflow file")
                print("  ❌ Empty workflow file")
                return

            self.workflows[filename] = content

            # Validate basic structure
            self._validate_structure(filename, content)

            # Validate triggers
            self._validate_triggers(filename, content)

            # Validate jobs
            self._validate_jobs(filename, content)

            # Validate permissions
            self._validate_permissions(filename, content)

            print(f"  ✅ YAML syntax valid")

        except yaml.YAMLError as e:
            self.errors.append(f"{filename}: YAML error - {str(e)}")
            print(f"  ❌ YAML error: {str(e)}")
        except Exception as e:
            self.errors.append(f"{filename}: Unexpected error - {str(e)}")
            print(f"  ❌ Unexpected error: {str(e)}")

    def _validate_structure(self, filename: str, content: Dict):
        """Validate basic workflow structure"""
        # Note: YAML parsers convert 'on' to boolean True
        has_name = 'name' in content
        has_on = 'on' in content or True in content  # YAML converts 'on' to True
        has_jobs = 'jobs' in content

        if not has_name:
            self.errors.append(f"{filename}: Missing required field 'name'")
            print(f"  ❌ Missing required field: name")
        else:
            print(f"  ✓ Has 'name' field")

        if not has_on:
            self.errors.append(f"{filename}: Missing required field 'on'")
            print(f"  ❌ Missing required field: on")
        else:
            print(f"  ✓ Has 'on' field (triggers)")

        if not has_jobs:
            self.errors.append(f"{filename}: Missing required field 'jobs'")
            print(f"  ❌ Missing required field: jobs")
        else:
            print(f"  ✓ Has 'jobs' field")

    def _validate_triggers(self, filename: str, content: Dict):
        """Validate workflow triggers"""
        # YAML converts 'on' to boolean True
        if 'on' not in content and True not in content:
            return

        # Get triggers (handle 'on' being converted to True)
        triggers = content.get('on', content.get(True))
        if isinstance(triggers, str):
            triggers = [triggers]
        elif isinstance(triggers, dict):
            triggers = list(triggers.keys())

        print(f"  ✓ Triggers: {', '.join(triggers)}")

        # Check for common trigger issues (handle both 'on' and True keys)
        trigger_config = content.get('on', content.get(True))
        if isinstance(trigger_config, dict):
            if 'push' in trigger_config and 'branches' in trigger_config['push']:
                branches = trigger_config['push']['branches']
                print(f"    - Push branches: {', '.join(branches)}")

            if 'pull_request' in trigger_config:
                pr_triggers = trigger_config['pull_request']
                if isinstance(pr_triggers, dict) and 'branches' in pr_triggers:
                    branches = pr_triggers['branches']
                    print(f"    - PR branches: {', '.join(branches)}")

            if 'schedule' in trigger_config:
                schedules = trigger_config['schedule']
                print(f"    - Scheduled: {len(schedules)} cron expression(s)")

    def _validate_jobs(self, filename: str, content: Dict):
        """Validate workflow jobs"""
        if 'jobs' not in content:
            return

        jobs = content['jobs']
        print(f"  ✓ Jobs: {len(jobs)}")

        for job_name, job_config in jobs.items():
            if not isinstance(job_config, dict):
                self.errors.append(f"{filename}: Job '{job_name}' is not a dictionary")
                continue

            # Check for required job fields
            if 'runs-on' not in job_config:
                self.errors.append(f"{filename}: Job '{job_name}' missing 'runs-on'")
                print(f"    ❌ Job '{job_name}': Missing 'runs-on'")
            else:
                runs_on = job_config['runs-on']
                print(f"    ✓ Job '{job_name}': runs on {runs_on}")

            # Check for steps
            if 'steps' in job_config:
                steps = job_config['steps']
                print(f"      - {len(steps)} steps")
            elif 'uses' not in job_config:
                self.warnings.append(f"{filename}: Job '{job_name}' has no steps or reusable workflow")

    def _validate_permissions(self, filename: str, content: Dict):
        """Validate workflow permissions"""
        if 'permissions' in content:
            perms = content['permissions']
            if isinstance(perms, dict):
                print(f"  ✓ Permissions: {', '.join(perms.keys())}")
            else:
                print(f"  ✓ Permissions: {perms}")
        else:
            self.warnings.append(f"{filename}: No explicit permissions set")

    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)

        print(f"\n✅ Validated workflows: {len(self.workflows)}")

        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ No errors found!")

        print("\n" + "=" * 70)

    def generate_workflow_matrix(self):
        """Generate a matrix of all workflows and their features"""
        print("\n📋 WORKFLOW FEATURE MATRIX")
        print("=" * 70)

        headers = ["Workflow", "Jobs", "Push", "PR", "Schedule", "Manual"]
        print(f"\n{headers[0]:<25} {headers[1]:<6} {headers[2]:<6} {headers[3]:<6} {headers[4]:<10} {headers[5]:<8}")
        print("-" * 70)

        for filename, content in sorted(self.workflows.items()):
            name = filename.replace('.yml', '').replace('.yaml', '')
            job_count = len(content.get('jobs', {}))

            # YAML converts 'on' to boolean True
            triggers = content.get('on', content.get(True, {}))
            if isinstance(triggers, str):
                triggers = {triggers: True}

            has_push = '✓' if 'push' in triggers else '✗'
            has_pr = '✓' if 'pull_request' in triggers or 'pull_request_target' in triggers else '✗'
            has_schedule = '✓' if 'schedule' in triggers else '✗'
            has_manual = '✓' if 'workflow_dispatch' in triggers else '✗'

            print(f"{name:<25} {job_count:<6} {has_push:<6} {has_pr:<6} {has_schedule:<10} {has_manual:<8}")

        print("=" * 70)

def main():
    validator = WorkflowValidator()

    # Validate all workflows
    is_valid = validator.validate_all()

    # Generate feature matrix
    validator.generate_workflow_matrix()

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
