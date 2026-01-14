#!/bin/bash
# Apply Perimeter CSS to space theme dashboard

# Copy space theme as base
cp generate_dashboard_space.py generate_dashboard.py

# Replace body background from dark space gradient to white
sed -i '' 's/background: linear-gradient.*100%);/background-color: {BRAND_OFF_WHITE};/' generate_dashboard.py
sed -i '' 's/background-size: 400% 400%;//' generate_dashboard.py
sed -i '' 's/animation: nebula-shift.*infinite;//' generate_dashboard.py
sed -i '' 's/color: #e0e6ed;/color: {BRAND_NAVY};/' generate_dashboard.py
sed -i '' 's/min-height: 100vh;//' generate_dashboard.py
sed -i '' 's/position: relative;//' generate_dashboard.py
sed -i '' 's/overflow-x: hidden;//' generate_dashboard.py

# Replace card background from dark/glowing to white
sed -i '' 's/background: rgba(9, 36, 63, 0.3);/background: white;/' generate_dashboard.py
sed -i '' 's/backdrop-filter: blur(15px);//' generate_dashboard.py
sed -i '' 's/box-shadow: 0 0 20px.*inset.*0.05);/box-shadow: 0 2px 8px rgba(0,0,0,0.1);/' generate_dashboard.py
sed -i '' 's/border: 2px solid rgba(96, 187, 233, 0.3);//' generate_dashboard.py
sed -i '' 's/opacity: 0;//' generate_dashboard.py
sed -i '' 's/animation: fade-in-up.*infinite;//' generate_dashboard.py

# Simplify header
sed -i '' 's/background: rgba.*blur(10px);/background: white;/' generate_dashboard.py

# Simplify text colors
sed -i '' 's/color: #a8c5da;/color: #6c757d;/' generate_dashboard.py
sed -i '' 's/color: #e0e6ed;/color: {BRAND_NAVY};/' generate_dashboard.py

echo "✅ Applied Perimeter CSS styling"
