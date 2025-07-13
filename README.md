# Implement Supply Chain Cost Comparison System
This commit introduces a comprehensive supply chain cost comparison tool with the following features:

- Added GUI interface using tkinter with Arabic support for supplier selection
- Implemented two cost calculation methods:
  * Company vehicle routing (TSP solution using Gurobi)
  * Individual supplier shipping with VAT calculation
- Created distance matrix processing from Excel files
- Added supplier and shipping type management system
- Implemented detailed cost comparison reporting with recommendations
- Designed intuitive UI with color-coded buttons and clear result display

Key components:
- Supplier mapping with Arabic names
- Shipping type configurations (carton, pallet, car parts)
- Cost parameter customization (vehicle cost, driver salary)
- TSP solver for optimal routing
- VAT calculation for shipping costs

The system helps optimize supply chain logistics by comparing centralized vs decentralized shipping methods.
