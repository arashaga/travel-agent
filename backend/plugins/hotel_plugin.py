from typing import Annotated

from semantic_kernel.functions import kernel_function

from modules.hotel_search import HotelSearcher


class HotelSearchPlugin:
    """Plugin for hotel search operations with comprehensive filtering options."""

    def __init__(self):
        self.searcher = HotelSearcher()

    @kernel_function(
        description="Search for hotels with comprehensive filtering options including price range, amenities, and guest ratings.",
        name="search_hotels",
    )
    def search_hotels(
        self,
        location: Annotated[str, "Hotel destination (city name, address, or landmark)"],
        check_in_date: Annotated[str, "Check-in date in YYYY-MM-DD format"],
        check_out_date: Annotated[str, "Check-out date in YYYY-MM-DD format"],
        adults: Annotated[str, "Number of adult guests (1-20)"] = "2",
        children: Annotated[str, "Number of children (0-10)"] = "0",
        rooms: Annotated[str, "Number of rooms needed (1-8)"] = "1",
        price_min: Annotated[str, "Minimum price per night in USD (empty string for no minimum)"] = "",
        price_max: Annotated[str, "Maximum price per night in USD (empty string for no maximum)"] = "",
        hotel_class: Annotated[str, "Hotel star rating (1-5, empty string for any)"] = "",
        amenities: Annotated[
            str,
            "Required amenities (comma-separated): 'wifi', 'pool', 'gym', 'spa', 'parking', 'breakfast', 'pet_friendly', 'business_center', 'room_service'",
        ] = "",
        min_rating: Annotated[str, "Minimum guest rating (1.0-5.0, empty string for any)"] = "",
        hotel_type: Annotated[
            str, "Type of accommodation: 'hotel', 'motel', 'resort', 'inn', 'hostel', 'apartment'"
        ] = "",
        cancellation_policy: Annotated[
            str, "Cancellation preference: 'free_cancellation', 'flexible', 'any'"
        ] = "any",
    ) -> str:
        try:
            def safe_int(value: str, default=None):
                if not value or value.strip() == "":
                    return default
                try:
                    return int(value.strip())
                except ValueError:
                    return default

            def safe_float(value: str, default=None):
                if not value or value.strip() == "":
                    return default
                try:
                    return float(value.strip())
                except ValueError:
                    return default

            def safe_str_list(value: str):
                if not value or value.strip() == "":
                    return []
                return [item.strip() for item in value.split(',') if item.strip()]

            adults_int = safe_int(adults, 2)
            children_int = safe_int(children, 0)
            rooms_int = safe_int(rooms, 1)
            price_min_int = safe_int(price_min)
            price_max_int = safe_int(price_max)
            hotel_class_int = safe_int(hotel_class)
            min_rating_float = safe_float(min_rating)
            amenities_list = safe_str_list(amenities)

            if adults_int is not None and adults_int < 1:
                adults_int = 1
            if adults_int is not None and adults_int > 20:
                adults_int = 20
            if children_int is not None and children_int > 10:
                children_int = 10
            if rooms_int is not None and rooms_int < 1:
                rooms_int = 1
            if rooms_int is not None and rooms_int > 8:
                rooms_int = 8

            if hotel_class_int is not None and (hotel_class_int < 1 or hotel_class_int > 5):
                hotel_class_int = None

            if min_rating_float is not None and (min_rating_float < 1.0 or min_rating_float > 5.0):
                min_rating_float = None

            valid_hotel_types = ['hotel', 'motel', 'resort', 'inn', 'hostel', 'apartment']
            if hotel_type and hotel_type not in valid_hotel_types:
                hotel_type = ""

            valid_cancellation = ['free_cancellation', 'flexible', 'any']
            if cancellation_policy not in valid_cancellation:
                cancellation_policy = 'any'

            results = self.searcher.search_hotels(
                location=location,
                checkin_date=check_in_date,
                checkout_date=check_out_date,
                adults=adults_int,
                children=children_int,
                rooms=rooms_int,
                min_price=price_min_int,
                max_price=price_max_int,
                amenities=amenities_list,
                min_rating=min_rating_float,
                property_types=[hotel_type] if hotel_type else None,
            )
            return self.searcher.format_hotel_results(results)
        except Exception as e:
            return f"Error searching hotels: {str(e)}"
