#!/usr/bin/env python3
"""
Google Flights Search Tool using SerpApi

This module provides a comprehensive FlightSearcher class for searching flights
using the Google Flights API via SerpApi with enhanced round-trip formatting.

Features:
- Round-trip and one-way flight searches
- Advanced filtering (price, time, airlines, layovers)
- Enhanced round-trip display with clear outbound/return separation
- Support for multiple passengers and travel classes
- Carbon emission information and price insights

Usage:
    from flight_search import FlightSearcher
    
    searcher = FlightSearcher()
    results = searcher.search_flights(
        departure_id="LAX",
        arrival_id="JFK",
        outbound_date="2025-07-15",
        return_date="2025-07-22",
        trip_type="round_trip"
    )
    formatted = searcher.format_flight_results(results)
    print(formatted)

For interactive exploration, use: notebooks/flight_search_examples.ipynb
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv


class FlightSearcher:
    """A class to search for flights using the SerpApi Google Flights API with enhanced formatting."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the FlightSearcher.
        
        Args:
            api_key (str): SerpApi API key. If not provided, will try to load from environment.
        """
        load_dotenv()
        
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('SERPAPI_API_KEY')
            
        if not self.api_key:
            raise ValueError("API key not found. Please set SERPAPI_API_KEY in .env file or environment variable.")
        
        self.base_url = "https://serpapi.com/search.json"
      
    def search_flights(
        self,
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        return_date: str = None,
        trip_type: str = "round_trip",
        travel_class: str = "economy",
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        departure_time_range: str = None,
        return_time_range: str = None,
        max_price: int = None,
        max_duration: int = None,
        min_layover_duration: int = None,
        max_layover_duration: int = None,
        include_airlines: List[str] = None,
        exclude_airlines: List[str] = None,
        currency: str = "USD",
        language: str = "en",
        country: str = "us",
        deep_search: bool = False,
        auto_fetch_return_flights: bool = True
    ) -> Dict:
        """
        Search for flights with enhanced round-trip support.
        
        Args:
            departure_id (str): IATA code for departure airport (e.g., 'LAX')
            arrival_id (str): IATA code for arrival airport (e.g., 'JFK')
            outbound_date (str): Departure date in YYYY-MM-DD format
            return_date (str): Return date in YYYY-MM-DD format (required for round-trip)
            trip_type (str): "round_trip" or "one_way"
            travel_class (str): "economy", "premium_economy", "business", "first"
            adults (int): Number of adult passengers
            children (int): Number of child passengers
            infants (int): Number of infant passengers
            departure_time_range (str): Time range for departure (e.g., "6,12" for 6AM-12PM)
            return_time_range (str): Time range for return (round-trip only)
            max_price (int): Maximum price filter
            max_duration (int): Maximum flight duration in hours
            min_layover_duration (int): Minimum layover duration in minutes
            max_layover_duration (int): Maximum layover duration in minutes
            include_airlines (List[str]): List of airline codes to include
            exclude_airlines (List[str]): List of airline codes to exclude
            currency (str): Currency code (default: "USD")
            language (str): Language code (default: "en")
            country (str): Country code (default: "us")
            deep_search (bool): Enable deep search for more results
            
        Returns:
            Dict: Flight search results with enhanced round-trip formatting
        """        # Map trip type to API values (correct mapping)
        type_mapping = {"one_way": 2, "round_trip": 1}
        
        # Map travel class to API values
        class_mapping = {
            "economy": 1,
            "premium_economy": 2,
            "business": 3,
            "first": 4
        }
        
        # Build base parameters
        params = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "departure_id": departure_id.upper(),
            "arrival_id": arrival_id.upper(),
            "outbound_date": outbound_date,
            "currency": currency,
            "hl": language,
            "gl": country,
        }
        
        # Add trip type
        params["type"] = type_mapping.get(trip_type, 1)
        
        # Handle return date for round-trip
        if trip_type == "round_trip":
            if not return_date:
                raise ValueError("Return date is required for round-trip searches")
            params["return_date"] = return_date
        elif return_date and trip_type == "one_way":
            # Warn if return date provided for one-way
            print("Warning: Return date ignored for one-way trip")
        
        # Add travel class
        params["travel_class"] = class_mapping.get(travel_class, 1)
        
        # Add passenger counts
        if adults > 0:
            params["adults"] = adults
        if children > 0:
            params["children"] = children
        if infants > 0:
            params["infants_in_seat"] = infants
        
        # Add time ranges
        if departure_time_range:
            params["outbound_times"] = departure_time_range
        if return_time_range and trip_type == "round_trip":
            params["return_times"] = return_time_range
        
        # Add layover duration
        if min_layover_duration and max_layover_duration:
            params["layover_duration"] = f"{min_layover_duration},{max_layover_duration}"
        
        # Add price and duration filters
        if max_price:
            params["max_price"] = max_price
        if max_duration:
            params["max_duration"] = max_duration
        
        # Add airline filters
        if include_airlines:
            params["include_airlines"] = ",".join(include_airlines)
        if exclude_airlines:
            params["exclude_airlines"] = ",".join(exclude_airlines)
        
        # Add deep search
        if deep_search:
            params["deep_search"] = True
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            results = response.json()
            if trip_type == "round_trip" and auto_fetch_return_flights and "best_flights" in results:
                outbound_params = {
                    "departure_id": departure_id.upper(),
                    "arrival_id": arrival_id.upper(),
                    "outbound_date": outbound_date,
                    "return_date": return_date,
                    "currency": currency,
                    "language": language,
                    "country": country,
                    "adults": adults,
                    "children": children,
                    "infants": infants,
                    "travel_class": travel_class,
                    "departure_time_range": departure_time_range,
                    "return_time_range": return_time_range,
                    "max_price": max_price,
                    "max_duration": max_duration,
                    "min_layover_duration": min_layover_duration,
                    "max_layover_duration": max_layover_duration,
                    "include_airlines": include_airlines,
                    "exclude_airlines": exclude_airlines,
                    "deep_search": deep_search
                }
                results = self._fetch_all_return_combinations(results, outbound_params)
            return results
        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse API response: {str(e)}"}

    def _fetch_all_return_combinations(self, initial_results: Dict, outbound_params: dict = None) -> Dict:
        """
        Fetch all return flight combinations for round-trip searches.
        
        Args:
            initial_results (Dict): Results from the initial outbound flight search
            outbound_params (dict): Original search params for outbound leg (optional, for multi_city_json)
            
        Returns:
            Dict: Enhanced results with all return flight combinations
        """
        if "best_flights" not in initial_results:
            return initial_results
        all_flights = []
        for flight in initial_results["best_flights"]:
            departure_token = flight.get("departure_token")
            if departure_token:
                try:
                    return_params = {
                        "engine": "google_flights",
                        "api_key": self.api_key,
                        "departure_token": departure_token
                    }
                    if outbound_params and outbound_params.get("return_date") and outbound_params.get("departure_id") and outbound_params.get("arrival_id"):
                        return_params["type"] = 3
                        return_params["currency"] = outbound_params.get("currency", "USD")
                        return_params["hl"] = outbound_params.get("language", "en")
                        return_params["gl"] = outbound_params.get("country", "us")
                        multi_city_json = [
                            {"departure_id": outbound_params["departure_id"], "arrival_id": outbound_params["arrival_id"], "date": outbound_params["outbound_date"]},
                            {"departure_id": outbound_params["arrival_id"], "arrival_id": outbound_params["departure_id"], "date": outbound_params["return_date"]}
                        ]
                        import json as _json
                        return_params["multi_city_json"] = _json.dumps(multi_city_json)
                    response = requests.get(self.base_url, params=return_params)
                    response.raise_for_status()
                    return_data = response.json()
                    return_flights = []
                    if "best_flights" in return_data:
                        return_flights.extend(return_data["best_flights"])
                    if "other_flights" in return_data:
                        return_flights.extend(return_data["other_flights"])
                    if not return_flights:
                        all_flights.append(flight)
                        continue
                    for idx, return_flight in enumerate(return_flights):
                        if return_flight.get("flights"):
                            combined_flight = flight.copy()
                            outbound_segments = combined_flight.get("flights", [])
                            return_segments = return_flight.get("flights", [])
                            combined_flight["flights"] = outbound_segments + return_segments
                            outbound_duration = combined_flight.get("total_duration", 0)
                            return_duration = return_flight.get("total_duration", 0)
                            if outbound_duration and return_duration:
                                combined_flight["total_duration"] = outbound_duration + return_duration
                            outbound_layovers = combined_flight.get("layovers", [])
                            return_layovers = return_flight.get("layovers", [])
                            combined_flight["layovers"] = outbound_layovers + return_layovers
                            combined_flight["_return_flight_info"] = {
                                "return_price": return_flight.get("price"),
                                "return_currency": return_flight.get("currency"),
                                "return_duration": return_flight.get("total_duration"),
                                "return_segments_count": len(return_segments)
                            }
                            if return_flight.get("price"):
                                combined_flight["price"] = return_flight["price"]
                            if return_flight.get("currency"):
                                combined_flight["currency"] = return_flight["currency"]
                            combined_flight["_return_option_index"] = idx + 1
                            all_flights.append(combined_flight)
                        else:
                            all_flights.append(flight)
                except Exception:
                    all_flights.append(flight)
            else:
                all_flights.append(flight)
        enhanced_results = initial_results.copy()
        enhanced_results["best_flights"] = all_flights
        if "other_flights" in enhanced_results:
            enhanced_results["other_flights"] = []
        return enhanced_results
    
    def _separate_round_trip_segments(self, flights: List[Dict]) -> List[Dict]:
        """
        Process round-trip flights to create separate outbound and return segments.
        
        Args:
            flights (List[Dict]): List of flight results
            
        Returns:
            List[Dict]: Enhanced flight data with separated round-trip segments
        """
        processed_flights = []
        
        for flight in flights:
            # Check if this is a round-trip flight with return flights
            if "return_flights" in flight and flight["return_flights"]:
                # Create outbound segment
                outbound = flight.copy()
                outbound["segment_type"] = "outbound"
                outbound["trip_type"] = "round_trip"
                processed_flights.append(outbound)
                
                # Create return segments
                for return_flight in flight["return_flights"]:
                    return_segment = return_flight.copy()
                    return_segment["segment_type"] = "return"
                    return_segment["trip_type"] = "round_trip"
                    return_segment["related_outbound"] = flight.get("flights", [{}])[0].get("flight_number", "N/A")
                    processed_flights.append(return_segment)
            else:
                # Single segment (one-way or outbound only)
                flight["segment_type"] = flight.get("segment_type", "outbound")
                flight["trip_type"] = flight.get("trip_type", "one_way")
                processed_flights.append(flight)
        
        return processed_flights
    
    def _format_flight_segment(self, flight: Dict) -> str:
        """
        Format a single flight segment with enhanced details.
        
        Args:
            flight (Dict): Flight data
            
        Returns:
            str: Formatted flight information
        """
        segment_type = flight.get("segment_type", "outbound")
        trip_type = flight.get("trip_type", "one_way")
        
        # Header with segment type
        if trip_type == "round_trip":
            header = f"✈️  {segment_type.upper()} FLIGHT"
            if segment_type == "return":
                related = flight.get("related_outbound", "N/A")
                header += f" (Return for {related})"
        else:
            header = "✈️  FLIGHT"
        
        # Price information
        price = flight.get("price", "N/A")
        
        # Flight details from the flights array
        flights_info = []
        if "flights" in flight:
            for i, f in enumerate(flight["flights"]):
                departure = f.get("departure_airport", {})
                arrival = f.get("arrival_airport", {})
                
                dep_code = departure.get("id", "N/A")
                dep_name = departure.get("name", "Unknown Airport")
                dep_time = f.get("departure_time", "N/A")
                
                arr_code = arrival.get("id", "N/A")
                arr_name = arrival.get("name", "Unknown Airport")
                arr_time = f.get("arrival_time", "N/A")
                
                airline = f.get("airline", "Unknown Airline")
                flight_number = f.get("flight_number", "N/A")
                aircraft = f.get("aircraft", "N/A")
                
                flight_info = f"""
  Flight {i+1}: {airline} {flight_number}
    • Route: {dep_code} ({dep_name}) → {arr_code} ({arr_name})
    • Times: {dep_time} → {arr_time}
    • Aircraft: {aircraft}"""
                
                flights_info.append(flight_info)
        
        # Duration and emissions
        duration = flight.get("total_duration", "N/A")
        emissions = flight.get("carbon_emissions", {})
        emissions_kg = emissions.get("this_flight", "N/A")
        emissions_diff = emissions.get("typical_for_this_route", "N/A")
        
        # Layovers
        layovers = []
        if "flights" in flight and len(flight["flights"]) > 1:
            for i in range(len(flight["flights"]) - 1):
                layover_info = f"Layover {i+1}: Details not available"
                layovers.append(f"    • {layover_info}")
        
        # Build the formatted string
        result = f"""
{header}
💰 Price: {price}
⏱️  Duration: {duration}
🌱 Emissions: {emissions_kg} kg CO₂ (vs typical: {emissions_diff})
{"".join(flights_info)}"""
        
        if layovers:
            result += f"\n  Layovers:\n" + "\n".join(layovers)
        
        return result    
    def format_flight_results(self, results: Dict) -> str:
        """
        Format flight search results with enhanced round-trip display.
        
        Args:
            results (Dict): Raw flight search results from the API
            
        Returns:
            str: Formatted flight results string
        """
        if "error" in results:
            return f"❌ Error: {results['error']}"
        
        if "best_flights" not in results or not results["best_flights"]:
            return "❌ No flights found for your search criteria."
        
        # Get search parameters for header
        search_params = results.get("search_parameters", {})
        departure_id = search_params.get("departure_id", "N/A")
        arrival_id = search_params.get("arrival_id", "N/A")
        outbound_date = search_params.get("outbound_date", "N/A")
        return_date = search_params.get("return_date")
        
        # Build header
        header = f"🔍 FLIGHT SEARCH RESULTS\n"
        header += f"📍 Route: {departure_id} → {arrival_id}\n"
        header += f"📅 Outbound: {outbound_date}\n"
        if return_date:
            header += f"📅 Return: {return_date}\n"
        header += "=" * 60 + "\n"
        
        # Process flights with round-trip separation
        flights = self._separate_round_trip_segments(results["best_flights"])
        
        # Format each flight
        formatted_flights = []
        for i, flight in enumerate(flights):
            formatted_flight = self._format_flight_segment(flight)
            formatted_flights.append(f"[Flight {i+1}]{formatted_flight}\n")
        
        # Additional information
        footer = f"\n📊 Total Results: {len(flights)} flight segments\n"
        
        # Price insights if available
        if "price_insights" in results:
            insights = results["price_insights"]
            footer += f"� Price Insights: {insights.get('lowest_price', 'N/A')} (lowest)\n"
        
        # Search metadata
        if "search_metadata" in results:
            metadata = results["search_metadata"]
            footer += f"⏱️  Search completed in {metadata.get('total_time_taken', 'N/A')}s\n"
        
        return header + "\n".join(formatted_flights) + footer


def main():
    """Example usage of the FlightSearcher class."""
    try:
        # Initialize the searcher
        searcher = FlightSearcher()
        
        # Example search
        results = searcher.search_flights(
            departure_id="LAX",
            arrival_id="JFK",
            outbound_date="2025-07-15",
            return_date="2025-07-22",
            trip_type="round_trip",
            adults=1
        )
        
        # Format and display results
        formatted_results = searcher.format_flight_results(results)
        print(formatted_results)
        
        # Save raw results for debugging
        with open("flight_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
