#!/usr/bin/env python3
"""
Team Capacity Dashboard
Run this anytime to see current capacity usage across all team members
"""
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env")

ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT}"}

# Team configuration
TEAM_CAPACITY = {
    "Zach Welliver": {"gid": "1205076276256605", "capacity": 50},
    "Nick Clark": {"gid": "1202206953008470", "capacity": 100},
    "Adriel Abella": {"gid": "1208249805795150", "capacity": 100},
    "John Meyer": {"gid": "1211292436943049", "capacity": 30}
}

# Projects
PROJECTS = {
    "Preproduction": "1208336083003480",
    "Production": "1209597979075357",
    "Post Production": "1209581743268502"
}

PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"

def get_capacity_usage():
    """Get current capacity usage for all team members"""
    capacity_usage = {name: {"total": 0, "tasks": []} for name in TEAM_CAPACITY.keys()}

    for project_name, project_gid in PROJECTS.items():
        endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,custom_fields,completed,assignee"
        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]

            for task in tasks:
                if task.get('completed', False):
                    continue

                assignee = task.get('assignee')
                if not assignee:
                    continue

                assignee_gid = assignee.get('gid')

                # Find which team member
                for member_name, member_info in TEAM_CAPACITY.items():
                    if member_info["gid"] == assignee_gid:
                        # Get allocation (Asana stores as decimal, multiply by 100 for percentage)
                        allocation = 0
                        for cf in task.get('custom_fields', []):
                            if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                                allocation = (cf.get('number_value', 0) or 0) * 100
                                break

                        if allocation > 0:
                            capacity_usage[member_name]["total"] += allocation
                            capacity_usage[member_name]["tasks"].append({
                                "name": task["name"],
                                "allocation": allocation,
                                "project": project_name
                            })
                        break
        except Exception as e:
            print(f"Error fetching {project_name}: {e}")

    return capacity_usage

def main():
    print("\n" + "="*70)
    print(f"TEAM CAPACITY DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)

    usage = get_capacity_usage()

    # Summary table
    print("\n📊 CAPACITY SUMMARY")
    print("-"*70)
    print(f"{'Team Member':<20} {'Usage':<15} {'Limit':<10} {'Status'}")
    print("-"*70)

    over_capacity = []
    for member_name, data in usage.items():
        total = data["total"]
        limit = TEAM_CAPACITY[member_name]["capacity"]
        percentage = (total / limit * 100) if limit > 0 else 0

        if total > limit:
            status = "⚠️  OVER CAPACITY"
            over_capacity.append(member_name)
        elif total > limit * 0.9:
            status = "⚡ Near Limit"
        elif total > limit * 0.75:
            status = "📈 High"
        else:
            status = "✅ OK"

        print(f"{member_name:<20} {total:>5.1f}% / {limit:>3d}%  ({percentage:>5.1f}%)  {status}")

    # Detailed breakdown
    print("\n" + "="*70)
    print("📋 DETAILED TASK BREAKDOWN")
    print("="*70)

    for member_name, data in usage.items():
        if data["tasks"]:
            print(f"\n{member_name} ({data['total']:.1f}%):")
            for task in sorted(data["tasks"], key=lambda x: x["allocation"], reverse=True):
                print(f"  • {task['allocation']:>5.1f}% - {task['name']} ({task['project']})")
        else:
            print(f"\n{member_name}: No active tasks")

    # Alerts
    if over_capacity:
        print("\n" + "="*70)
        print("⚠️  CAPACITY ALERTS")
        print("="*70)
        for member in over_capacity:
            total = usage[member]["total"]
            limit = TEAM_CAPACITY[member]["capacity"]
            print(f"❌ {member} is OVER CAPACITY: {total:.1f}% (limit: {limit}%)")

    print("\n" + "="*70)
    print()

if __name__ == "__main__":
    main()
