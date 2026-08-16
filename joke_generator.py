#!/usr/bin/env python3
"""
Random Joke Generator
Fetches and displays random jokes from the Official Joke API.
Supports multiple joke types and categories.
"""

import requests
import sys
from typing import Optional, Dict, Any


class JokeGenerator:
    """Generate random jokes using the Official Joke API."""
    
    BASE_URL = "https://official-joke-api.appspot.com"
    
    def __init__(self, timeout: int = 5):
        """Initialize the joke generator.
        
        Args:
            timeout: Request timeout in seconds (default: 5)
        """
        self.timeout = timeout
    
    def get_random_joke(self) -> Optional[Dict[str, Any]]:
        """Fetch a random joke from any category.
        
        Returns:
            Dictionary containing joke data or None if request fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/random_joke",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching joke: {e}", file=sys.stderr)
            return None
    
    def get_joke_by_type(self, joke_type: str) -> Optional[Dict[str, Any]]:
        """Fetch a random joke of a specific type.
        
        Args:
            joke_type: Type of joke ('general' or 'knock-knock')
        
        Returns:
            Dictionary containing joke data or None if request fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/jokes/{joke_type}/random",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()[0]  # API returns a list
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {joke_type} joke: {e}", file=sys.stderr)
            return None
    
    def get_multiple_jokes(self, count: int = 5) -> Optional[list]:
        """Fetch multiple random jokes.
        
        Args:
            count: Number of jokes to fetch (default: 5)
        
        Returns:
            List of joke dictionaries or None if request fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/jokes/random/{count}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jokes: {e}", file=sys.stderr)
            return None
    
    @staticmethod
    def format_joke(joke: Dict[str, Any]) -> str:
        """Format a joke for display.
        
        Args:
            joke: Joke dictionary from API
        
        Returns:
            Formatted joke string
        """
        if "setup" in joke and "punchline" in joke:
            return f"{joke['setup']}\n{joke['punchline']}"
        elif "joke" in joke:
            return joke["joke"]
        return "Unable to format joke"
    
    @staticmethod
    def display_joke(joke: Dict[str, Any]) -> None:
        """Display a joke nicely formatted.
        
        Args:
            joke: Joke dictionary from API
        """
        formatted = JokeGenerator.format_joke(joke)
        print(f"\n{'='*50}")
        print(formatted)
        print(f"{'='*50}\n")


def main():
    """Main function to demonstrate the joke generator."""
    generator = JokeGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "random":
            print("🎭 Fetching a random joke...\n")
            joke = generator.get_random_joke()
            if joke:
                generator.display_joke(joke)
        
        elif command == "general":
            print("😄 Fetching a general joke...\n")
            joke = generator.get_joke_by_type("general")
            if joke:
                generator.display_joke(joke)
        
        elif command == "knock-knock":
            print("🚪 Fetching a knock-knock joke...\n")
            joke = generator.get_joke_by_type("knock-knock")
            if joke:
                generator.display_joke(joke)
        
        elif command == "multiple":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            print(f"😂 Fetching {count} random jokes...\n")
            jokes = generator.get_multiple_jokes(count)
            if jokes:
                for i, joke in enumerate(jokes, 1):
                    print(f"Joke #{i}:")
                    generator.display_joke(joke)
        
        elif command == "help":
            print_help()
        
        else:
            print(f"Unknown command: {command}")
            print_help()
    
    else:
        # Default: fetch and display a random joke
        print("🎭 Fetching a random joke...\n")
        joke = generator.get_random_joke()
        if joke:
            generator.display_joke(joke)
        else:
            print("Failed to fetch a joke. Please try again later.")


def print_help():
    """Print help information."""
    help_text = """
Random Joke Generator - Usage:

  python joke_generator.py [command] [options]

Commands:
  random              Fetch a single random joke (default)
  general             Fetch a general-type joke
  knock-knock         Fetch a knock-knock joke
  multiple [count]    Fetch multiple jokes (default: 5)
  help                Show this help message

Examples:
  python joke_generator.py
  python joke_generator.py general
  python joke_generator.py knock-knock
  python joke_generator.py multiple 10
  python joke_generator.py help

API: Official Joke API (https://official-joke-api.appspot.com)
    """
    print(help_text)


if __name__ == "__main__":
    main()
