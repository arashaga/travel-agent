#!/usr/bin/env python3
"""
Google Hotels Search Tool using SerpApi

This module provides a HotelSearcher class for searching hotels
using the Google Hotels API via SerpApi with enhanced formatting.

Features:
- Search for hotels by location, check-in/check-out, guests, and filters
- Advanced filtering (price, amenities, star rating, property type)
- Support for multiple guests and rooms
- Enhanced display of hotel details and offers

Usage:
    from hotel_search import HotelSearcher
    
    searcher = HotelSearcher()
    results = searcher.search_hotels(
        location="New York",
        checkin_date="2025-07-15",
        checkout_date="2025-07-18",
        adults=2
    )
    formatted = searcher.format_hotel_results(results)
    print(formatted)

For interactive exploration, use: notebooks/hotel_search_examples.ipynb
"""

import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path

class HotelSearcher:
    """A class to search for hotels using the SerpApi Google Hotels API with enhanced formatting."""
    
    def __init__(self, api_key: str = None):
        dotenv_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(dotenv_path=dotenv_path, override=True)
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("API key not found. Please set SERPAPI_API_KEY in .env file or environment variable.")
        self.base_url = "https://serpapi.com/search"

    def search_hotels(
        self,
        location: str,
        checkin_date: str,
        checkout_date: str,
        adults: int = 1,
        children: int = 0,
        rooms: int = 1,
        currency: str = "USD",
        language: str = "en",
        country: str = "us",
        min_price: int = None,
        max_price: int = None,
        min_rating: float = None,
        max_rating: float = None,
        amenities: List[str] = None,
    property_types: List[str] = None
    ) -> Dict:
        """
        Search for hotels with specified parameters.
        Args:
            location (str): City or location name (e.g., 'New York')
            checkin_date (str): Check-in date in YYYY-MM-DD format
            checkout_date (str): Check-out date in YYYY-MM-DD format
            adults (int): Number of adult guests
            children (int): Number of child guests
            rooms (int): Number of rooms
            currency (str): Currency code (default: 'USD')
            language (str): Language code (default: 'en')
            country (str): Country code (default: 'us')
            min_price (int): Minimum price filter
            max_price (int): Maximum price filter
            min_rating (float): Minimum star rating
            max_rating (float): Maximum star rating
            amenities (List[str]): List of amenities to filter (e.g., ['wifi', 'pool'])
            property_types (List[str]): List of property types (e.g., ['hotel', 'apartment'])
        Returns:
            Dict: Hotel search results
        """
        params = {
            "engine": "google_hotels",
            "api_key": self.api_key,
            "q": location,
            "check_in_date": checkin_date,
            "check_out_date": checkout_date,
            "adults": adults,
            "children": children,
            "rooms": rooms,
            "currency": currency,
            "hl": language,
            "gl": country
        }
        if min_price:
            params["min_price"] = min_price
        if max_price:
            params["max_price"] = max_price
        if min_rating:
            params["min_rating"] = min_rating
        if max_rating:
            params["max_rating"] = max_rating
        if amenities:
            params["amenities"] = ",".join(amenities)
        if property_types:
            params["type"] = ",".join(property_types)
    # Note: sort_by is intentionally not supported/passed to the API.
        try:
            safe_params = dict(params)
            if "api_key" in safe_params and isinstance(safe_params["api_key"], str):
                k = safe_params["api_key"]
                safe_params["api_key"] = (k[:4] + "..." + k[-4:]) if len(k) > 8 else "***"
            print(f"[HotelSearcher] params: {safe_params}")      # <-- ADD 1
            response = requests.get(self.base_url, params=params, timeout=60) 
            print(f"[HotelSearcher] GET {response.url} -> {response.status_code}") 
            response.raise_for_status()

            results = response.json()
            # ADD: surface SerpAPI status + counts
            meta = results.get("search_metadata", {}) or {}
            status = meta.get("status")
            sid = meta.get("id")
            err = results.get("error")
            props = len(results.get("properties") or [])
            print(f"[HotelSearcher] serpapi status={status} id={sid} error={err} properties={props}")  # <-- ADD 3

            if status != "Success" or err:
                # Bubble an informative error so the agent shows a useful message
                return {"error": f"SerpAPI error: status={status} err={err} id={sid}"}

            return results

        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, "response", None) is not None else ""
            raise Exception(f"HTTP {getattr(e.response,'status_code','?')} for {response.url}\n{body}") from e
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse API response: {str(e)}"}
        except Exception as e:
            # ADD: catch everything else so the agent doesn’t just say “technical issue”
            return {"error": f"Hotel search failed: {str(e)}"}    # <-- ADD 4


    def format_hotel_results(self, results: Dict) -> str:
        """
        Format hotel search results for display.
        Args:
            results (Dict): Raw hotel search results from the API
        Returns:
            str: Formatted hotel results string
        """
        if "error" in results:
            return f"❌ Error: {results['error']}"
        
        # Google Hotels API uses 'properties' for hotel results
        hotels = results.get("properties", [])
        if not hotels:
            return "❌ No hotels found for your search criteria."
        
        # Header with search parameters
        search_params = results.get('search_parameters', {})
        header = f"🔍 HOTEL SEARCH RESULTS\n"
        header += f"📍 Location: {search_params.get('q', 'N/A')}\n"
        header += f"📅 Check-in: {search_params.get('check_in_date', 'N/A')}\n"
        header += f"📅 Check-out: {search_params.get('check_out_date', 'N/A')}\n"
        header += f"👥 Guests: {search_params.get('adults', 'N/A')} adults, {search_params.get('children', 0)} children\n"
        header += "=" * 60 + "\n"
        
        formatted_hotels = []
        for i, hotel in enumerate(hotels):
            # Basic info
            name = hotel.get("name", "N/A")
            hotel_type = hotel.get("type", "hotel")
            description = hotel.get("description", "")
            
            # Price information
            rate_per_night = hotel.get("rate_per_night", {})
            total_rate = hotel.get("total_rate", {})
            
            price_per_night = rate_per_night.get("lowest", "N/A") if rate_per_night else "N/A"
            total_price = total_rate.get("lowest", "N/A") if total_rate else "N/A"
            
            # Rating and reviews
            rating = hotel.get("overall_rating", "N/A")
            reviews = hotel.get("reviews", "N/A")
            location_rating = hotel.get("location_rating", "N/A")
            
            # Hotel class/stars
            hotel_class = hotel.get("hotel_class", "")
            
            # Amenities (show top 5)
            amenities = hotel.get("amenities", [])
            amenities_str = ", ".join(amenities[:5]) if amenities else "None listed"
            if len(amenities) > 5:
                amenities_str += f" (and {len(amenities) - 5} more)"
            
            # Deal information
            deal = hotel.get("deal", "")
            
            # Check-in/out times
            check_in = hotel.get("check_in_time", "N/A")
            check_out = hotel.get("check_out_time", "N/A")
            
            # Link
            link = hotel.get("link", "")
            
            formatted = f"[Hotel {i+1}] 🏨 {name}\n"
            if hotel_type != "hotel":
                formatted += f"  🏠 Type: {hotel_type.title()}\n"
            if description:
                formatted += f"  � {description[:100]}{'...' if len(description) > 100 else ''}\n"
            if hotel_class:
                formatted += f"  ⭐ Class: {hotel_class}\n"
            formatted += f"  💰 Price per night: {price_per_night}\n"
            formatted += f"  💵 Total price: {total_price}\n"
            if deal:
                formatted += f"  🎯 Deal: {deal}\n"
            formatted += f"  ⭐ Rating: {rating}/5.0 ({reviews} reviews)\n"
            if location_rating != "N/A":
                formatted += f"  � Location rating: {location_rating}/5.0\n"
            formatted += f"  �🛎️  Amenities: {amenities_str}\n"
            formatted += f"  🕐 Check-in: {check_in} | Check-out: {check_out}\n"
            if link:
                formatted += f"  🔗 Book: {link}\n"
            formatted += "\n"
            
            formatted_hotels.append(formatted)
        
        footer = f"📊 Total Results: {len(hotels)} hotels\n"
        return header + "\n".join(formatted_hotels) + footer

def main():
    """Example usage of the HotelSearcher class with Rome, Italy example."""
    try:
        print("🏛️ ROME HOTEL SEARCH EXAMPLE")
        print("=" * 40)
        print("Using HotelSearcher module to search for hotels in Rome, Italy...")
        print()
        
        searcher = HotelSearcher()
        
        # Search for hotels in Rome, Italy
        results = searcher.search_hotels(
            location="Rome, Italy",
            checkin_date="2025-09-15",
            checkout_date="2025-09-18",
            adults=2,
            currency="EUR",
            language="en",
            country="it"
        )
        
        # Format and display results
        formatted_results = searcher.format_hotel_results(results)
        print(formatted_results)
        
        # Save results to file
        with open("rome_hotel_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n💾 Results saved to 'rome_hotel_results.json'")
        
        # Show some quick statistics
        properties = results.get("properties", [])
        if properties:
            print(f"\n📊 QUICK STATS:")
            print(f"🏨 Hotels found: {len(properties)}")
            
            # Count property types
            types = {}
            for prop in properties:
                prop_type = prop.get("type", "hotel")
                types[prop_type] = types.get(prop_type, 0) + 1
            
            print(f"🏠 Property types: {', '.join([f'{k}: {v}' for k, v in types.items()])}")
            
        print("\n✅ Rome hotel search completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure you have:")
        print("  - Set SERPAPI_API_KEY in your .env file")
        print("  - Installed required dependencies: requests, python-dotenv")
        print("  - Valid internet connection")

if __name__ == "__main__":
    main()
