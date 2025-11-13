#!/usr/bin/env python3
"""
Dashboard Data Loader

Reads all weekly reports and bundles them into a JavaScript file for the dashboard.
Creates both historical data (weeks 1-4) and separate week 5 data for manual loading demo.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class DashboardDataLoader:
    """Loads and formats data for the dashboard."""
    
    def __init__(self):
        self.dashboard_data_dir = Path("dashboard_data")
        self.student_names_file = Path("student_names.json")
        self.output_dir = Path("dashboard")
        
    def load_student_names(self) -> Dict[str, str]:
        """Load student name mappings."""
        if self.student_names_file.exists():
            with open(self.student_names_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def load_week_data(self, week_num: int) -> Dict[str, Any]:
        """Load all reports for a specific week."""
        week_dir = self.dashboard_data_dir / f"week{week_num}"
        reports_dir = week_dir / "reports"
        
        if not reports_dir.exists():
            return {}
        
        week_data = {}
        for report_file in reports_dir.glob("*_report.json"):
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
                student_id = report['student_id']
                week_data[student_id] = report
        
        return week_data
    
    def create_dashboard_data(self, weeks: List[int]) -> Dict[str, Any]:
        """Create consolidated dashboard data structure."""
        student_names = self.load_student_names()
        
        # Structure: {student_id: {name: str, grade: int, weekly_data: [{week, data}, ...]}}
        dashboard_data = {}
        
        for week in weeks:
            week_data = self.load_week_data(week)
            
            for student_id, report in week_data.items():
                if student_id not in dashboard_data:
                    dashboard_data[student_id] = {
                        'student_id': student_id,
                        'name': student_names.get(student_id, student_id),
                        'grade_level': report['grade_level'],
                        'weekly_reports': []
                    }
                
                dashboard_data[student_id]['weekly_reports'].append({
                    'week': week,
                    'report_date': report['report_date'],
                    'week_number': report.get('week_number', week),
                    'proficiency_score': report['vocabulary_profile']['proficiency_score'],
                    'vocabulary_richness': report['vocabulary_profile']['vocabulary_richness'],
                    'academic_word_ratio': report['vocabulary_profile']['academic_word_ratio'],
                    'avg_sentence_length': report['vocabulary_profile']['avg_sentence_length'],
                    'unique_words': report['vocabulary_profile']['unique_words'],
                    'recommendations': report['vocabulary_recommendations'],
                    'sample_count': report['metadata']['sample_count']
                })
        
        return dashboard_data
    
    def write_js_file(self, data: Dict[str, Any], filename: str, var_name: str = "DASHBOARD_DATA"):
        """Write data as JavaScript file."""
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("// Auto-generated dashboard data\n")
            f.write("// Do not edit manually\n\n")
            f.write(f"const {var_name} = ")
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
            f.write(";\n")
        
        print(f"✓ Created {output_file}")
        return output_file
    
    def generate_all_data_files(self):
        """Generate all required data files for the dashboard."""
        print("Generating dashboard data files...")
        print()
        
        # Historical data (weeks 1-4)
        print("Loading historical data (weeks 1-4)...")
        historical_data = self.create_dashboard_data([1, 2, 3, 4])
        self.write_js_file(historical_data, "dashboard_data.js")
        print(f"  Loaded {len(historical_data)} students")
        print()
        
        # Week 5 data (for manual loading)
        print("Loading week 5 data...")
        week5_data = self.create_dashboard_data([5])
        self.write_js_file(week5_data, "week5_data.js", "WEEK5_DATA")
        print(f"  Loaded {len(week5_data)} students")
        print()
        
        # Statistics
        total_reports = sum(len(s['weekly_reports']) for s in historical_data.values())
        total_recommendations = sum(
            len(week['recommendations']) 
            for student in historical_data.values() 
            for week in student['weekly_reports']
        )
        
        print("Summary:")
        print(f"  Total students: {len(historical_data)}")
        print(f"  Total historical reports: {total_reports}")
        print(f"  Total recommendations: {total_recommendations}")
        print()
        print("Dashboard data generation complete!")


def main():
    """Main entry point."""
    loader = DashboardDataLoader()
    loader.generate_all_data_files()
    
    print()
    print("Next steps:")
    print("  1. Open dashboard/index.html in a web browser")
    print("  2. Or run: python3 -m http.server 8000 (then visit http://localhost:8000/dashboard/)")


if __name__ == "__main__":
    main()

