from typing import Annotated, List, Optional

from semantic_kernel.functions import kernel_function

# Import helper without modifying it
from modules.flight_search import FlightSearcher


class FlightSearchPlugin:
    """Plugin for flight search operations with comprehensive parameter mapping."""

    def __init__(self):
        self.searcher = FlightSearcher()
        self.class_mapping = {
            "economy": "economy",
            "premium economy": "premium_economy",
            "business": "business",
            "first": "first",
            "first class": "first",
            "business class": "business",
            "premium": "premium_economy",
            "coach": "economy",
        }
        self.airline_codes = {
            "american": "AA",
            "united": "UA",
            "delta": "DL",
            "southwest": "WN",
            "jetblue": "B6",
            "alaska": "AS",
            "frontier": "F9",
            "spirit": "NK",
            "air canada": "AC",
            "lufthansa": "LH",
            "british airways": "BA",
            "air france": "AF",
            "klm": "KL",
            "emirates": "EK",
            "qatar": "QR",
            "etihad": "EY",
            "turkish": "TK",
            "aeromexico": "AM",
            "latam": "LA",
            "avianca": "AV",
            "copa": "CM",
            "aerolineas argentinas": "AR",
            "qantas": "QF",
            "air new zealand": "NZ",
            "japan airlines": "JL",
            "ana": "NH",
            "singapore": "SQ",
            "cathay pacific": "CX",
            "eva air": "BR",
            "china airlines": "CI",
            "china southern": "CZ",
            "china eastern": "MU",
            "air india": "AI",
            "indigo": "6E",
            "thai": "TG",
            "malaysia": "MH",
            "philippine airlines": "PR",
            "korean air": "KE",
            "asiana": "OZ",
            "saudia": "SV",
            "egyptair": "MS",
            "ethiopian": "ET",
            "kenya airways": "KQ",
            "south african": "SA",
            "el al": "LY",
            "austrian": "OS",
            "swiss": "LX",
            "brussels": "SN",
            "finnair": "AY",
            "norwegian": "DY",
            "iberia": "IB",
            "tap portugal": "TP",
            "alitalia": "AZ",
            "aeroflot": "SU",
            "lot": "LO",
            "sas": "SK",
            "icelandair": "FI",
            "air europa": "UX",
            "vueling": "VY",
            "easyjet": "U2",
            "ryanair": "FR",
            "wizz air": "W6",
            "pegasus": "PC",
            "garuda indonesia": "GA",
            "vietjet": "VJ",
            "air asia": "AK",
            "bangkok airways": "PG",
            "scoot": "TR",
            "jetstar": "JQ",
            "virgin atlantic": "VS",
            "virgin australia": "VA",
            "azul": "AD",
            "gol": "G3",
            "air china": "CA",
            "hainan": "HU",
            "shenzhen": "ZH",
            "oman air": "WY",
            "kuwait airways": "KU",
            "qatar airways": "QR",
            "emirates airline": "EK",
            "air tahiti nui": "TN",
            "fiji airways": "FJ",
            "hawaiian": "HA",
            "westjet": "WS",
            "sunwing": "WG",
            "air transat": "TS",
        }

    @kernel_function(
        description=
        "Search for flights with comprehensive filtering options. Supports both one-way and round-trip searches.",
        name="search_flights",
    )
    def search_flights(
        self,
        departure_airport: Annotated[str, "IATA code for departure airport (e.g., 'LAX', 'JFK')"],
        arrival_airport: Annotated[str, "IATA code for arrival airport (e.g., 'LAX', 'JFK')"],
        departure_date: Annotated[str, "Departure date in YYYY-MM-DD format"],
        return_date: Annotated[
            str, "Return date in YYYY-MM-DD format (required for round-trip, empty string for one-way)"
        ] = "",
        trip_type: Annotated[str, "Trip type: 'round_trip' or 'one_way'"] = "round_trip",
        travel_class: Annotated[
            str, "Travel class: 'economy', 'premium_economy', 'business', 'first'"
        ] = "economy",
        adults: Annotated[str, "Number of adult passengers (1-9)"] = "1",
        children: Annotated[str, "Number of child passengers (0-8)"] = "0",
        infants: Annotated[str, "Number of infant passengers (0-8)"] = "0",
        max_price: Annotated[str, "Maximum price limit in USD (empty string for no limit)"] = "",
        max_duration: Annotated[str, "Maximum flight duration in minutes (empty string for no limit)"] = "",
        preferred_airlines: Annotated[
            str, "Comma-separated list of preferred airline names or codes (empty string for none)"
        ] = "",
        excluded_airlines: Annotated[
            str, "Comma-separated list of excluded airline names or codes (empty string for none)"
        ] = "",
        max_stops: Annotated[
            str, "Maximum number of stops (0 for nonstop, 1 for one stop, etc. Empty string for no limit)"
        ] = "",
        departure_time_preference: Annotated[
            str, "Departure time preference: 'morning', 'afternoon', 'evening' (empty string for any time)"
        ] = "",
        return_time_preference: Annotated[
            str, "Return time preference: 'morning', 'afternoon', 'evening' (empty string for any time)"
        ] = "",
        deep_search: Annotated[bool, "Enable deep search for more comprehensive results"] = True,
    ) -> str:
        try:
            def safe_int(value: str, default=None):
                if not value or value.strip() == "":
                    return default
                try:
                    return int(value.strip())
                except ValueError:
                    return default

            def safe_str_or_none(value: str):
                if not value or value.strip() == "":
                    return None
                return value.strip()

            adults_int = safe_int(adults, 1)
            children_int = safe_int(children, 0)
            infants_int = safe_int(infants, 0)
            max_price_int = safe_int(max_price)
            max_duration_int = safe_int(max_duration)
            max_stops_int = safe_int(max_stops)

            return_date_processed = safe_str_or_none(return_date)
            mapped_class = self.class_mapping.get(travel_class.lower(), travel_class)

            include_airlines = None
            exclude_airlines = None
            if preferred_airlines and preferred_airlines.strip():
                airlines = [a.strip() for a in preferred_airlines.split(',')]
                include_airlines = [self.airline_codes.get(a.lower(), a.upper()) for a in airlines]
            if excluded_airlines and excluded_airlines.strip():
                airlines = [a.strip() for a in excluded_airlines.split(',')]
                exclude_airlines = [self.airline_codes.get(a.lower(), a.upper()) for a in airlines]

            time_range_mapping = {
                "morning": "6,12",
                "afternoon": "12,18",
                "evening": "18,23",
            }
            departure_time_range = None
            return_time_range = None
            if departure_time_preference and departure_time_preference.strip():
                departure_time_range = time_range_mapping.get(departure_time_preference.lower())
            if return_time_preference and return_time_preference.strip():
                return_time_range = time_range_mapping.get(return_time_preference.lower())

            results = self.searcher.search_flights(
                departure_id=departure_airport,
                arrival_id=arrival_airport,
                outbound_date=departure_date,
                return_date=return_date_processed,
                trip_type=trip_type,
                travel_class=mapped_class,
                adults=adults_int,
                children=children_int,
                infants=infants_int,
                departure_time_range=departure_time_range,
                return_time_range=return_time_range,
                max_price=max_price_int,
                max_duration=max_duration_int,
                include_airlines=include_airlines,
                exclude_airlines=exclude_airlines,
                stops=max_stops_int,
                deep_search=deep_search,
                auto_fetch_return_flights=True,
            )
            return self.searcher.format_flight_results(results)
        except Exception as e:
            return f"Error searching flights: {str(e)}"
