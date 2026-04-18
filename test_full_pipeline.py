
import os
import sys
import time
from orchestrator import ContentOrchestrator
from utils.logger import log

def run_test():
    """Run a full end-to-end test of the LinkedIn content pipeline."""
    log.info("Starting Full Pipeline Integration Test")
    
    # 1. Initialize Orchestrator
    log.info("Step 1: Initializing Orchestrator")
    orch = ContentOrchestrator()
    
    # 2. Run Research for a test topic
    log.info("Step 2: Running Research for test topic")
    test_url = "https://www.nugen.com/about"
    test_industry = "Digital Marketing Automation"
    
    # Clear any existing approved topics to avoid noise (optional)
    # orch.run_daily_research(url=test_url, industry=test_industry)
    
    # 3. Simulate User Approval
    log.info("Step 3: Simulating Trello Approval (Finding and Moving latest topic)")
    topics_list = orch.trello.topics_list.list_cards()
    if not topics_list:
        log.info("No topics found in 'Topics' list. Running research first...")
        orch.run_daily_research(url=test_url, industry=test_industry)
        topics_list = orch.trello.topics_list.list_cards()
    
    if topics_list:
        latest_card = topics_list[0]
        log.info(f"Moving card '{latest_card.name}' to Approved Topics")
        latest_card.change_list(orch.trello.approved_topics_list.id)
    else:
        log.error("Failed to find or create topics. Test aborted.")
        return

    # 4. Process Approved Topics
    log.info("Step 4: Processing Approved Topics (Content + Creative)")
    orch.process_approved_topics()
    
    log.info("Step 5: Process Approved Content (Publishing/Archiving)")
    # We might not want to actually post to LinkedIn, but let's see
    orch.publish_approved_content()

    log.info("Full Pipeline Test Completed!")

if __name__ == "__main__":
    run_test()
