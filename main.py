import sys
import time
import signal
import logging
import argparse
from pathlib import Path

import config
from agent.orchestrator import StudyAgentOrchestrator
from whatsapp.session import WhatsAppSession
from whatsapp.listener import WhatsAppListener
from whatsapp.sender import WhatsAppSender

# Configure clean, informative logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("whatsapp_agent.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("StudyAgent")

def run_cli_test(orchestrator: StudyAgentOrchestrator, query: str):
    """Test the agent brain directly from CLI without opening WhatsApp."""
    print(f"\n🎓 === Testing Study Agent with Query: '{query}' ===")
    response = orchestrator.process_message(query)
    
    print("\n--- WhatsApp Text Summary ---")
    print(response.text_message)
    print("\n--- Generated Attachments ---")
    if response.attachment_paths:
        for p in response.attachment_paths:
            print(f"  📎 {p}")
    else:
        print("  (No attachments generated)")
    print("===================================================\n")


def main():
    parser = argparse.ArgumentParser(description="WhatsApp Student Notes & Study AI Agent")
    parser.add_argument("--test", type=str, help="Run a test query directly via CLI (bypasses WhatsApp)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (use after QR is scanned)")
    args = parser.parse_args()

    # 1. Validate API keys
    is_valid, missing_keys = config.validate_keys()
    if not is_valid and not args.test:
        print("\n" + "=" * 60)
        print("⚠️  MISSING API KEYS!")
        print(f"Please populate the following keys in your .env file: {', '.join(missing_keys)}")
        print("Copy .env.example to .env and add your OpenRouter and Serper keys:")
        print("  cp .env.example .env")
        print("=" * 60 + "\n")
        if not args.test:
            sys.exit(1)

    # 2. Initialize Agent Orchestrator
    orchestrator = StudyAgentOrchestrator(
        openrouter_api_key=config.OPENROUTER_API_KEY,
        serper_api_key=config.SERPER_API_KEY,
        model=config.OPENROUTER_MODEL,
        output_dir=config.OUTPUT_DIR
    )

    # If running CLI test mode
    if args.test:
        run_cli_test(orchestrator, args.test)
        return

    # 3. Initialize WhatsApp Session
    headless = args.headless or config.HEADLESS_BROWSER
    session = WhatsAppSession(
        profile_dir=config.CHROME_PROFILE_DIR,
        headless=headless
    )

    # Register graceful shutdown handlers
    def handle_sigint(sig, frame):
        logger.info("\nShutting down gracefully...")
        session.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        driver = session.start()
        print("\n" + "*" * 65)
        print("📲 WhatsApp Web is starting...")
        print("If this is your first run, please scan the QR code in the browser.")
        print("*" * 65 + "\n")

        if not session.wait_for_login(timeout=180):
            logger.error("Failed to authenticate with WhatsApp Web. Exiting.")
            session.close()
            sys.exit(1)

        listener = WhatsAppListener(driver, allowed_chats=config.ALLOWED_CHATS)
        sender = WhatsAppSender(driver)

        logger.info("🚀 Study Agent is now ACTIVE!")
        print("\n" + "=" * 65)
        print("🔒 STRICT PRIVACY SHIELD ACTIVE:")
        print(f"  Only listening to authorized chat(s): {config.ALLOWED_CHATS_RAW}")
        print("  The agent will NEVER touch, open, or reply to any other chat or group.")
        print("=" * 65 + "\n")

        # Seed existing last message so bot doesn't re-trigger on old chat history
        active_title = listener.get_active_chat_title()
        if active_title:
            seed_msg = listener.get_latest_user_message()
            if seed_msg:
                listener.processed_signatures.add((active_title, seed_msg))
                logger.info(f"Initialized chat history for '{active_title}'. Ready for new student queries!")

        # Main Polling Loop
        while True:
            msg = listener.check_for_unread_message()
            if msg:
                print(f"\n📩 New message from [{msg.chat_title}]: \"{msg.text}\"")

                # Send quick acknowledgment and register text to avoid self-reply loop
                ack_text = "🔍 *Looking up academic resources & preparing your study notes... please hold on a moment!* 📚"
                listener.register_bot_message(ack_text)
                sender.send_text(ack_text)

                try:
                    # Process query through Agent Orchestrator
                    agent_res = orchestrator.process_message(msg.text)

                    # Send text summary and register
                    listener.register_bot_message(agent_res.text_message)
                    sender.send_text(agent_res.text_message)

                    # Send document attachments (PDF, DOCX, PPTX)
                    for attachment_file in agent_res.attachment_paths:
                        time.sleep(1.0)
                        sender.send_attachment(attachment_file)

                    logger.info(f"Finished processing request from {msg.chat_title}.")

                except Exception as req_err:
                    logger.error(f"Error processing request from {msg.chat_title}: {req_err}", exc_info=True)
                    error_msg = (
                        "⚠️ *Sorry, an error occurred while generating notes!*\n"
                        "If you are on the OpenRouter free tier, please wait 30 seconds before sending your next topic so the budget settles."
                    )
                    listener.register_bot_message(error_msg)
                    sender.send_text(error_msg)

            time.sleep(config.POLL_INTERVAL_SECONDS)

    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        session.close()

if __name__ == "__main__":
    main()
