#!/usr/bin/env python3
"""
WAHA API Scheduler
Script untuk menjalankan automasi WAHA API secara periodik
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse
import json
import os
from waha_automator import WahaAPIClient


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('waha_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WahaScheduler:
    """
    Scheduler untuk automasi WAHA API
    """

    def __init__(self, config_file: str = "waha_config.json"):
        """
        Initialize scheduler

        Args:
            config_file: Path ke file konfigurasi
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.client = WahaAPIClient(
            base_url=self.config.get('base_url', 'http://localhost:3000'),
            username=self.config.get('username', 'admin'),
            password=self.config.get('password', 'e44213b43dc349709991dbb1a6343e47'),
            api_key=self.config.get('api_key', 'c79b6529186c44aa9d536657ffea710b')
        )
        self.last_run_times = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load konfigurasi dari file

        Returns:
            Dict: Konfigurasi
        """
        default_config = {
            "base_url": "http://localhost:3000",
            "username": "admin",
            "password": "e44213b43dc349709991dbb1a6343e47",
            "api_key": "c79b6529186c44aa9d536657ffea710b",
            "output_dir": "output",
            "chats": [
                {
                    "chat_id": "6282243673017@c.us",
                    "name": "Primary Chat",
                    "enabled": True,
                    "limit": 100,
                    "sort_by": "timestamp",
                    "sort_order": "desc"
                }
            ],
            "schedule": {
                "interval_minutes": 30,
                "enabled_hours": {
                    "start": "08:00",
                    "end": "22:00"
                }
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with default config untuk completeness
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Dict[str, Any]):
        """
        Save konfigurasi ke file

        Args:
            config: Konfigurasi yang akan disimpan
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config file: {e}")

    def is_within_enabled_hours(self) -> bool:
        """
        Check if current time is within enabled hours

        Returns:
            bool: True if within enabled hours
        """
        schedule_config = self.config.get('schedule', {})
        enabled_hours = schedule_config.get('enabled_hours', {})

        if not enabled_hours:
            return True  # 24/7 jika tidak ada batasan

        try:
            start_time = datetime.strptime(enabled_hours.get('start', '00:00'), '%H:%M').time()
            end_time = datetime.strptime(enabled_hours.get('end', '23:59'), '%H:%M').time()
            current_time = datetime.now().time()

            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                # Handle overnight schedule (e.g., 22:00 to 08:00)
                return current_time >= start_time or current_time <= end_time

        except Exception as e:
            logger.error(f"Error checking enabled hours: {e}")
            return True

    def fetch_chat_messages(self, chat_config: Dict[str, Any]) -> bool:
        """
        Fetch messages untuk satu chat

        Args:
            chat_config: Konfigurasi chat

        Returns:
            bool: True jika berhasil
        """
        chat_id = chat_config['chat_id']
        chat_name = chat_config.get('name', chat_id)

        logger.info(f"📡 Fetching messages for chat: {chat_name} ({chat_id})")

        try:
            # Get messages
            response_data = self.client.get_chat_messages(
                chat_id=chat_id,
                limit=chat_config.get('limit', 100),
                offset=0,
                sort_by=chat_config.get('sort_by', 'timestamp'),
                sort_order=chat_config.get('sort_order', 'desc')
            )

            if response_data:
                # Save to file
                saved_file = self.client.save_response_to_file(
                    data=response_data,
                    chat_id=chat_id,
                    output_dir=self.config.get('output_dir', 'output')
                )

                # Update last run time
                self.last_run_times[chat_id] = datetime.now()

                # Log summary
                messages = response_data.get('messages', [])
                logger.info(f"✅ Successfully saved {len(messages)} messages to {saved_file}")

                # Check if there are new messages
                if self.has_new_messages(response_data):
                    logger.info(f"🆕 New messages detected for {chat_name}")

                return True
            else:
                logger.error(f"❌ Failed to fetch messages for {chat_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error fetching messages for {chat_name}: {e}")
            return False

    def has_new_messages(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if there are new messages based on timestamp

        Args:
            response_data: Response dari WAHA API

        Returns:
            bool: True jika ada messages baru
        """
        messages = response_data.get('messages', [])
        if not messages:
            return False

        # Get latest message timestamp
        latest_message = messages[0]  # Assuming sorted by timestamp desc
        latest_timestamp = latest_message.get('timestamp', 0)

        # Compare with last run time (convert to seconds)
        if latest_message.get('chat_id') in self.last_run_times:
            last_run_timestamp = int(self.last_run_times[latest_message['chat_id']].timestamp())
            return latest_timestamp > last_run_timestamp

        return True  # Assume new if no previous run

    def run_scheduled_fetch(self):
        """
        Run scheduled fetch for all enabled chats
        """
        if not self.is_within_enabled_hours():
            logger.info("⏸️ Outside enabled hours, skipping fetch")
            return

        logger.info("🚀 Starting scheduled fetch...")

        chats = self.config.get('chats', [])
        enabled_chats = [chat for chat in chats if chat.get('enabled', True)]

        if not enabled_chats:
            logger.warning("⚠️ No enabled chats found")
            return

        success_count = 0
        total_count = len(enabled_chats)

        for chat_config in enabled_chats:
            if self.fetch_chat_messages(chat_config):
                success_count += 1
            else:
                logger.warning(f"⚠️ Failed to fetch messages for {chat_config.get('name', chat_config['chat_id'])}")

        logger.info(f"📊 Fetch completed: {success_count}/{total_count} chats successful")

    def setup_scheduler(self):
        """
        Setup schedule berdasarkan konfigurasi
        """
        schedule_config = self.config.get('schedule', {})
        interval_minutes = schedule_config.get('interval_minutes', 30)

        logger.info(f"⏰ Setting up scheduler to run every {interval_minutes} minutes")
        logger.info(f"🕐 Enabled hours: {schedule_config.get('enabled_hours', '24/7')}")

        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.run_scheduled_fetch)

        # Run once immediately
        logger.info("🏃 Running initial fetch...")
        self.run_scheduled_fetch()

    def start(self):
        """
        Start the scheduler
        """
        logger.info("🚀 Starting WAHA Scheduler...")
        logger.info(f"📋 Configuration: {json.dumps(self.config, indent=2)}")

        self.setup_scheduler()

        logger.info("⏳ Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            raise


def create_sample_config():
    """Create sample configuration file"""
    config = {
        "base_url": "http://localhost:3000",
        "username": "admin",
        "password": "e44213b43dc349709991dbb1a6343e47",
        "api_key": "c79b6529186c44aa9d536657ffea710b",
        "output_dir": "output",
        "chats": [
            {
                "chat_id": "6282243673017@c.us",
                "name": "Primary Chat",
                "enabled": True,
                "limit": 100,
                "sort_by": "timestamp",
                "sort_order": "desc"
            },
            {
                "chat_id": "628123456789@c.us",
                "name": "Secondary Chat",
                "enabled": False,
                "limit": 50,
                "sort_by": "timestamp",
                "sort_order": "desc"
            }
        ],
        "schedule": {
            "interval_minutes": 30,
            "enabled_hours": {
                "start": "08:00",
                "end": "22:00"
            }
        }
    }

    with open('waha_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("📄 Sample configuration created: waha_config.json")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='WAHA API Scheduler')

    parser.add_argument('--config', default='waha_config.json',
                       help='Configuration file path (default: waha_config.json)')
    parser.add_argument('--create-config', action='store_true',
                       help='Create sample configuration file')
    parser.add_argument('--test-run', action='store_true',
                       help='Run once for testing')
    parser.add_argument('--interval', type=int, default=30,
                       help='Override schedule interval in minutes')

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()

    if args.create_config:
        create_sample_config()
        return 0

    if args.test_run:
        # Test run: fetch once and exit
        scheduler = WahaScheduler(args.config)
        scheduler.run_scheduled_fetch()
        return 0

    # Override interval if specified
    if args.interval:
        scheduler = WahaScheduler(args.config)
        scheduler.config['schedule']['interval_minutes'] = args.interval
        logger.info(f"⏰ Using custom interval: {args.interval} minutes")

    # Start scheduler
    scheduler = WahaScheduler(args.config)
    scheduler.start()

    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)