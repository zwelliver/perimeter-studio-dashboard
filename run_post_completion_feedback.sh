#!/bin/bash
# Run the Post-Completion Feedback Collection
# Posts completion summaries and effort feedback requests on completed Post Production tasks

cd "$(dirname "$0")"
source venv/bin/activate
python3 post_completion_feedback.py
