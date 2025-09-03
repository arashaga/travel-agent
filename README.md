# Google Flights Search Tool

A comprehensive Python tool for searching flights using the Google Flights API via SerpApi. Features **enhanced round-trip flight formatting** with clear separation of outbound and return flights, plus both command-line and Jupyter notebook interfaces.
you can use this repo as a refrence to turn it into MCP https://github.com/Azure-Samples/azure-ai-travel-agents?tab=readme-ov-file#preview-the-application-locally-for-free

## ✨ Recent Improvements

🎯 **Enhanced Round-Trip Flight Display**
- Clear visual separation of outbound (🛫) and return (🛬) flights
- Intelligent segment separation algorithm for complex multi-connection flights
- Enhanced flight details including amenities, legroom, and delay warnings
- Professional airline-style formatting with emojis and better organization

## Features

✈️ **Comprehensive Flight Search**
- Round-trip, one-way, and multi-city flights
- Multiple passengers (adults, children, infants)
- Travel class selection (economy, premium, business, first)
- Departure and arrival time preferences
- Layover duration control
- Price and duration filtering
- Airline inclusion/exclusion
- Deep search for accurate results

🎨 **Enhanced Formatting**
- **Clear outbound vs return flight separation** for round-trip searches
- Visual indicators (🛫/🛬) for flight direction
- Detailed amenity information and warnings
- Professional, airline-style result display
- Smart layover organization with overnight indicators

🔐 **Secure Configuration**
- Environment variable loading with `python-dotenv`
- API key protection through `.env` file
- No hardcoded credentials

📊 **Multiple Interfaces**
- **Jupyter notebook for exploratory analysis** ⭐ **(Recommended)**
- Command-line interface for scripting
- Interactive command-line mode
- Formatted output and result saving

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd travel-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# SerpApi API Key for Google Flights
SERPAPI_API_KEY=your_serpapi_key_here
```

Get your free API key from [SerpApi](https://serpapi.com/).

### 3. Choose Your Interface

#### 🌟 Option A: Jupyter Notebook (Recommended)

```bash
# Install Jupyter if not already installed
pip install jupyter

# Start Jupyter
jupyter notebook

# Open notebooks/flight_search_examples.ipynb
```

The notebook includes:
- ✅ **Complete FlightSearcher implementation** 
- ✅ **Step-by-step examples** with detailed explanations
- ✅ **Basic and advanced flight searches**
- ✅ **Family travel scenarios**
- ✅ **Utility functions** for result analysis
- ✅ **Tips and best practices**
- ✅ **Proper dotenv integration**

#### Option B: Quick Environment Check

```bash
# Check if your environment is set up correctly
python flight_search.py

# Run the test script
python test_dotenv.py
```

### 4. Test Your Setup

```bash
# Verify environment variables are loaded correctly
python test_dotenv.py
```

## Notebook Examples

The Jupyter notebook (`notebooks/flight_search_examples.ipynb`) includes these comprehensive examples:

1. **Basic Round-Trip Search**: AUS to JFK with standard parameters
2. **Advanced Filtered Search**: Business class with time/price/airline filters  
3. **Enhanced Round-Trip Formatting**: Demonstrates improved outbound/return display
4. **Family Travel**: One-way flight with multiple passengers and budget constraints
5. **Utility Functions**: Save results, extract deals, compare prices

Each example demonstrates different aspects of the API and shows how to handle various travel scenarios.

### 🎯 Round-Trip Flight Formatting Improvements

The notebook now features enhanced formatting for round-trip flights that makes complex itineraries much easier to understand:

**Before**: All flight segments listed chronologically
```
Flight Details:
  Segment 1: American AA 1234 (AUS → DFW)
  Segment 2: American AA 5678 (DFW → LAX)  
  Segment 3: Southwest WN 9012 (LAX → PHX)
  Segment 4: Southwest WN 3456 (PHX → AUS)
```

**After**: Clear separation of outbound and return journeys
```
🛫 OUTBOUND FLIGHTS:
  🛫 Segment 1: American AA 1234
    Route: AUS (08:30) → DFW (09:45)
    Duration: 1h 15m | Aircraft: Boeing 737
    Amenities: Wi-Fi, In-seat power, Snacks

🛬 RETURN FLIGHTS:
  🛬 Segment 1: Southwest WN 9012
    Route: LAX (14:15) → PHX (16:45)
    Duration: 1h 30m | Aircraft: Boeing 737-800
    ⚠️  Often delayed by 30+ minutes
    Amenities: Free Wi-Fi, 2 free bags
```

**Key Benefits:**
- ✅ **Visual clarity** with 🛫 outbound and 🛬 return indicators
- ✅ **Enhanced details** including legroom, amenities, and warnings
- ✅ **Smart separation** algorithm for complex multi-connection flights
- ✅ **Better planning** - see each journey direction clearly
- ✅ **Professional formatting** similar to airline booking systems

You can see this in action by running the demo:
```bash
python round_trip_formatting_demo.py
```

## Environment Variables with dotenv

The application uses `python-dotenv` to securely load environment variables:

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access your API key
api_key = os.getenv('SERPAPI_API_KEY')
```

## API Parameters

### Required Parameters
- `departure_id`: Airport code (e.g., 'LAX', 'JFK')
- `arrival_id`: Destination airport code
- `outbound_date`: Departure date (YYYY-MM-DD)

### Optional Parameters
- `return_date`: Return date for round-trip flights
- `trip_type`: 'round_trip', 'one_way', or 'multi_city'
- `adults`, `children`, `infants`: Passenger counts
- `travel_class`: 'economy', 'premium_economy', 'business', 'first'
- `departure_time_range`: Time range (e.g., '6,18' for 6AM-6PM)
- `max_price`: Maximum ticket price
- `include_airlines`: List of preferred airline codes
- `exclude_airlines`: List of airlines to avoid
- `max_duration`: Maximum flight duration in minutes
- `deep_search`: Enable for more accurate results

## Project Structure

```
travel-agent/
├── flight_search.py          # Quick start guide and env check
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables (create this)
├── test_dotenv.py           # Test script for setup verification
├── README.md                # This file
├── notebooks/
│   ├── flight_search_examples.ipynb  # 🌟 Complete interactive examples
│   └── test.ipynb          # Additional notebook
└── docs/                   # API documentation
```

**Important**: The main FlightSearcher implementation is in the Jupyter notebook (`notebooks/flight_search_examples.ipynb`) rather than a separate Python file. This design choice provides:

- ✅ **Better learning experience** with step-by-step examples
- ✅ **Interactive exploration** of different flight search scenarios  
- ✅ **Self-contained functionality** - everything works within the notebook
- ✅ **No import path issues** - complete implementation in one place## Programmatic Usage

```python
from flight_search import FlightSearcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize searcher
searcher = FlightSearcher()

# Search for flights
results = searcher.search_flights(
    departure_id="LAX",
    arrival_id="JFK",
    outbound_date="2025-07-15",
    return_date="2025-07-22",
    adults=2,
    travel_class="economy",
    max_price=800,
    departure_time_range="6,18"  # 6AM to 6PM
)

# Format and display results
formatted_results = searcher.format_flight_results(results)
print(formatted_results)
```

## Command Line Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--departure` | `-d` | Departure airport code | `-d LAX` |
| `--arrival` | `-a` | Arrival airport code | `-a JFK` |
| `--outbound-date` | `-o` | Departure date (YYYY-MM-DD) | `-o 2025-07-15` |
| `--return-date` | `-r` | Return date (YYYY-MM-DD) | `-r 2025-07-22` |
| `--trip-type` | `-t` | Trip type (round_trip/one_way) | `-t one_way` |
| `--adults` | | Number of adults | `--adults 2` |
| `--children` | | Number of children | `--children 1` |
| `--infants` | | Number of infants | `--infants 1` |
| `--travel-class` | `-c` | Travel class | `-c business` |
| `--max-price` | | Maximum price in USD | `--max-price 1000` |
| `--deep-search` | | Enable deep search | `--deep-search` |
| `--interactive` | `-i` | Interactive mode | `-i` |

## Tips for Better Results

🎯 **Flexible Dates**: Use dates ±3 days for better price options  
✈️ **Nearby Airports**: Consider alternative airports in large cities  
⏰ **Advance Booking**: 6-8 weeks for domestic, 2-3 months for international  
💡 **Deep Search**: Use `deep_search=True` for more accurate results  
🔄 **Filter Combinations**: Experiment with different filter combinations  

## Troubleshooting

### Common Issues

**"API key not found"**
- Ensure `.env` file exists in project root
- Verify `SERPAPI_API_KEY` is set correctly in `.env`
- Check for typos in the environment variable name
- Run `python test_dotenv.py` to verify setup

**"No flights found"**
- Try broader search criteria
- Check airport codes are valid (3-letter IATA codes)
- Ensure dates are in the future
- Remove restrictive filters

**"API request failed"**
- Check internet connection
- Verify API key is valid and has credits
- Check SerpApi status page
- Try reducing search complexity

### Environment Setup

1. **Check .env file**:
   ```bash
   # File should contain:
   SERPAPI_API_KEY=your_actual_api_key_here
   ```

2. **Verify dependencies**:
   ```bash
   pip list | grep -E "(requests|python-dotenv)"
   ```

3. **Test configuration**:
   ```bash
   python test_dotenv.py
   ```

## Getting Started with the Notebook

1. **Install Jupyter** (if not already installed):
   ```bash
   pip install jupyter
   ```

2. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

3. **Open the example notebook**:
   - Navigate to `notebooks/`
   - Open `flight_search_examples.ipynb`
   - Run all cells to see the examples in action

4. **Experiment**:
   - Modify the examples for your needs
   - Try different airports and dates
   - Experiment with various filter combinations

## Example Output

```
================================================================================
FLIGHT SEARCH RESULTS
================================================================================

Search Parameters:
  Route: LAX → JFK
  Outbound: 2025-07-15
  Return: 2025-07-22
  Currency: USD

Price Insights:
  Lowest Price: 298 USD
  Price Level: typical
  Typical Range: 250 - 450 USD

==================== BEST FLIGHTS ====================

--- Flight Option 1 ---
Price: 298 USD
Total Duration: 10h 30m
Type: Round trip
Carbon Emissions: 1234 kg
  (+15% vs typical)

Flight Details:
  Segment 1: American Airlines AA123
    LAX (08:00) → JFK (16:30)
    Duration: 5h 30m
    Aircraft: Boeing 737-800
    Class: Economy
```

## Requirements

- Python 3.7+
- requests
- python-dotenv
- jupyter (for notebook interface)

## License

This project is for educational and personal use. Please respect SerpApi's terms of service and rate limits.

---

**🚀 Quick Start: Run `python test_dotenv.py` then open `notebooks/flight_search_examples.ipynb` for an interactive experience!**
