#!/usr/bin/env python3
"""
Test Data Generator for Prompt Platform

This script creates comprehensive test data including:
- Multiple prompt lineages with versions
- Training examples for DSPy testing
- Various prompt types and scenarios
- Performance metrics data
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.database import PromptDB, Example, Prompt
from prompt_platform.schemas import Prompt as PromptSchema

def create_test_prompts():
    """Create comprehensive test data for the prompt platform."""
    
    db = PromptDB()
    
    # Test prompt data with various scenarios
    test_prompts = [
        {
            "task": "Email Writing Assistant",
            "prompt": """You are a professional email writing assistant. Help users write clear, professional emails.

Input: {input}

Guidelines:
- Use professional tone
- Be concise but complete
- Include appropriate greetings and closings
- Check for clarity and grammar""",
            "training_data": [
                {"input": "I need to write an email to my boss asking for a day off", 
                 "output": "Subject: Request for Personal Day\n\nDear [Boss's Name],\n\nI hope this email finds you well. I am writing to request a personal day on [specific date] due to [brief reason].\n\nI have ensured that my current projects are up to date and will coordinate with my team to cover any urgent matters during my absence.\n\nThank you for considering my request. I look forward to hearing from you.\n\nBest regards,\n[Your Name]"},
                {"input": "Write an email to a client apologizing for a delay", 
                 "output": "Subject: Apology for Project Delay\n\nDear [Client Name],\n\nI hope you're doing well. I wanted to personally reach out to apologize for the delay in delivering [project name].\n\nWe understand the importance of meeting deadlines, and I want to assure you that we are working diligently to complete the project as soon as possible. The new delivery date will be [new date].\n\nWe appreciate your patience and understanding. Please don't hesitate to reach out if you have any questions.\n\nBest regards,\n[Your Name]"},
                {"input": "Email to schedule a meeting with colleagues", 
                 "output": "Subject: Meeting Request - [Topic]\n\nHi Team,\n\nI hope everyone is having a great week. I'd like to schedule a meeting to discuss [specific topic] and get everyone's input.\n\nProposed time: [date and time]\nDuration: [estimated duration]\nLocation: [meeting room or virtual link]\n\nPlease let me know if this time works for you or if you'd prefer an alternative.\n\nLooking forward to our discussion.\n\nBest regards,\n[Your Name]"}
            ]
        },
        {
            "task": "Code Review Assistant",
            "prompt": """You are an expert code reviewer. Analyze the provided code and provide constructive feedback.

Input: {input}

Review Guidelines:
- Check for best practices
- Identify potential bugs
- Suggest improvements
- Consider performance implications
- Ensure code readability""",
            "training_data": [
                {"input": "def calculate_average(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total / len(numbers)", 
                 "output": "**Code Review Feedback:**\n\n**Issues Found:**\n1. **Division by zero risk**: No check for empty list\n2. **Type safety**: No validation for numeric input\n3. **Performance**: Could use built-in sum() function\n\n**Suggested Improvements:**\n```python\ndef calculate_average(numbers):\n    if not numbers:\n        raise ValueError('Cannot calculate average of empty list')\n    if not all(isinstance(x, (int, float)) for x in numbers):\n        raise TypeError('All elements must be numeric')\n    return sum(numbers) / len(numbers)\n```\n\n**Best Practices Applied:**\n- Input validation\n- Error handling\n- Use of built-in functions\n- Clear error messages"},
                {"input": "function getUserData(userId) {\n    fetch('/api/users/' + userId)\n        .then(response => response.json())\n        .then(data => console.log(data));\n}", 
                 "output": "**Code Review Feedback:**\n\n**Issues Found:**\n1. **Security**: Potential XSS with direct string concatenation\n2. **Error handling**: No error handling for failed requests\n3. **Async/await**: Could use modern async/await syntax\n4. **Return value**: Function doesn't return anything\n\n**Suggested Improvements:**\n```javascript\nasync function getUserData(userId) {\n    try {\n        const response = await fetch(`/api/users/${encodeURIComponent(userId)}`);\n        if (!response.ok) {\n            throw new Error(`HTTP error! status: ${response.status}`);\n        }\n        const data = await response.json();\n        return data;\n    } catch (error) {\n        console.error('Error fetching user data:', error);\n        throw error;\n    }\n}\n```\n\n**Best Practices Applied:**\n- Input sanitization\n- Proper error handling\n- Modern async/await syntax\n- Meaningful return values"}
            ]
        },
        {
            "task": "Content Summarizer",
            "prompt": """You are a content summarization expert. Create concise, accurate summaries of the provided content.

Input: {input}

Summary Guidelines:
- Capture key points and main ideas
- Maintain accuracy and objectivity
- Use clear, concise language
- Include important details and context
- Aim for 20-30% of original length""",
            "training_data": [
                {"input": "The rapid advancement of artificial intelligence has transformed various industries, from healthcare to finance. Machine learning algorithms can now diagnose diseases with higher accuracy than human doctors in some cases, while AI-powered trading systems execute millions of transactions per second. However, this progress also raises concerns about job displacement and ethical implications. Experts suggest that while AI will automate many routine tasks, it will also create new job opportunities and enhance human capabilities rather than replace them entirely.", 
                 "output": "**Summary:**\n\nAI advancement has revolutionized healthcare and finance, with machine learning achieving superior diagnostic accuracy and enabling high-frequency trading. While concerns exist about job displacement, experts believe AI will augment human capabilities and create new opportunities rather than replace human workers entirely."},
                {"input": "Climate change represents one of the most pressing challenges of our time. Rising global temperatures, melting polar ice caps, and increasing frequency of extreme weather events all point to the urgent need for action. Scientists agree that human activities, particularly the burning of fossil fuels, are the primary drivers of climate change. Solutions include transitioning to renewable energy sources, improving energy efficiency, and implementing carbon pricing mechanisms. International cooperation is essential, as climate change affects all nations regardless of their contribution to the problem.", 
                 "output": "**Summary:**\n\nClimate change, driven primarily by human fossil fuel consumption, presents urgent global challenges including rising temperatures and extreme weather. Solutions require renewable energy transition, energy efficiency improvements, and international cooperation to address this universal threat."}
            ]
        },
        {
            "task": "Business Plan Generator",
            "prompt": """You are a business consultant. Help users create comprehensive business plans for their ideas.

Input: {input}

Business Plan Guidelines:
- Include executive summary
- Define target market and competition
- Outline marketing strategy
- Provide financial projections
- Address potential risks and mitigation""",
            "training_data": [
                {"input": "I want to start a mobile app for food delivery from local restaurants", 
                 "output": "**Business Plan: LocalEats Mobile App**\n\n**Executive Summary:**\nLocalEats connects customers with local restaurants for food delivery, focusing on supporting small businesses and providing fresh, local cuisine.\n\n**Target Market:**\n- Urban professionals aged 25-45\n- Food enthusiasts seeking local options\n- Small restaurant owners\n\n**Competitive Analysis:**\n- Differentiate from major chains by focusing on local restaurants\n- Offer lower commission rates to attract small businesses\n- Emphasize community support and sustainability\n\n**Marketing Strategy:**\n- Social media campaigns highlighting local partnerships\n- Community events and food festivals\n- Referral programs for both customers and restaurants\n\n**Financial Projections:**\n- Year 1: $500K revenue, 15% commission model\n- Year 2: $1.2M revenue, expanded market\n- Year 3: $2.5M revenue, multiple cities\n\n**Risk Mitigation:**\n- Diversify restaurant partnerships\n- Implement quality control measures\n- Maintain strong customer service"},
                {"input": "Create a business plan for an online tutoring platform", 
                 "output": "**Business Plan: EduConnect Online Tutoring Platform**\n\n**Executive Summary:**\nEduConnect provides personalized online tutoring services connecting qualified tutors with students worldwide, offering flexible scheduling and diverse subject coverage.\n\n**Target Market:**\n- K-12 students seeking academic support\n- College students needing subject-specific help\n- Adult learners pursuing skill development\n- International students\n\n**Competitive Analysis:**\n- Offer 24/7 availability\n- Provide AI-powered matching\n- Include progress tracking and analytics\n- Support multiple languages\n\n**Marketing Strategy:**\n- Partner with educational institutions\n- SEO and content marketing\n- Student referral programs\n- Social media presence on educational platforms\n\n**Financial Projections:**\n- Year 1: $300K revenue, 20% platform fee\n- Year 2: $800K revenue, expanded subjects\n- Year 3: $1.5M revenue, international expansion\n\n**Risk Mitigation:**\n- Rigorous tutor vetting process\n- Quality assurance systems\n- Customer satisfaction guarantees\n- Insurance coverage"}
            ]
        }
    ]
    
    print("🔄 Creating test prompts with training data...")
    
    for i, prompt_data in enumerate(test_prompts):
        # Create multiple versions for each prompt to simulate improvement history
        lineage_id = str(uuid.uuid4())
        parent_id = None
        
        for version in range(1, 4):  # Create 3 versions
            # Create prompt data
            prompt_dict = {
                "id": str(uuid.uuid4()),
                "lineage_id": lineage_id,
                "parent_id": parent_id,
                "task": prompt_data["task"],
                "prompt": prompt_data["prompt"],
                "version": version,
                "training_data": json.dumps(prompt_data["training_data"]),  # Store as JSON string
                "improvement_request": f"Version {version} - Improved for better clarity and effectiveness" if version > 1 else None,
                "generation_process": f"Generated using systematic prompt engineering principles. Version {version} includes refinements based on user feedback and testing.",
                "created_at": time.time() - (version - 1) * 86400,  # Each version 1 day apart
                "model": "gpt-4"
            }
            
            # Save the prompt
            saved_prompt = db.save_prompt(prompt_dict)
            
            # Add training examples to the database
            for example in prompt_data["training_data"]:
                db.add_example(
                    prompt_id=saved_prompt["id"],
                    input_text=example["input"],
                    output_text=example["output"],
                    critique="Good example - demonstrates effective prompt usage"
                )
            
            # Set parent_id for next version
            parent_id = saved_prompt["id"]
            
            print(f"✅ Created {prompt_data['task']} v{version} with {len(prompt_data['training_data'])} training examples")
    
    print(f"🎉 Successfully created {len(test_prompts)} prompt lineages with training data!")

def create_performance_data():
    """Create additional performance metrics data."""
    
    db = PromptDB()
    
    # Get existing prompts to add more examples
    existing_prompts = db.get_all_prompts()
    
    if not existing_prompts:
        print("⚠️ No existing prompts found. Run create_test_prompts() first.")
        return
    
    print("🔄 Adding performance data and additional examples...")
    
    # Add more training examples to existing prompts
    additional_examples = [
        {
            "input": "Write a professional email to decline a job offer",
            "output": "Subject: Thank You - Job Offer Response\n\nDear [Hiring Manager Name],\n\nThank you for offering me the [Position Title] role at [Company Name]. I appreciate the time you and your team spent throughout the interview process.\n\nAfter careful consideration, I have decided to decline the offer. This was not an easy decision, but I believe it's the right choice for my career goals at this time.\n\nI have great respect for [Company Name] and the work you do. I hope our paths cross again in the future.\n\nThank you again for the opportunity.\n\nBest regards,\n[Your Name]"
        },
        {
            "input": "Review this Python function for security issues:\ndef process_user_input(user_data):\n    query = 'SELECT * FROM users WHERE id = ' + user_data\n    return execute_query(query)",
            "output": "**Security Review - Critical Issues Found:**\n\n**🚨 CRITICAL: SQL Injection Vulnerability**\nThe function is vulnerable to SQL injection attacks. Direct string concatenation allows malicious input to modify the query.\n\n**Vulnerable Code:**\n```python\ndef process_user_input(user_data):\n    query = 'SELECT * FROM users WHERE id = ' + user_data  # VULNERABLE\n    return execute_query(query)\n```\n\n**Secure Solution:**\n```python\ndef process_user_input(user_data):\n    query = 'SELECT * FROM users WHERE id = %s'\n    return execute_query(query, (user_data,))\n```\n\n**Additional Recommendations:**\n- Validate input data types\n- Use parameterized queries\n- Implement input sanitization\n- Add error handling\n- Consider using an ORM"
        },
        {
            "input": "Summarize the key findings of a research study on remote work productivity",
            "output": "**Research Summary: Remote Work Productivity Study**\n\n**Key Findings:**\n- Remote workers show 13% higher productivity compared to office workers\n- Reduced commute time contributes to better work-life balance\n- Technology infrastructure quality directly impacts productivity\n- Hybrid models show optimal results for team collaboration\n\n**Methodology:**\n12-month study with 2,000 participants across 50 companies\n\n**Implications:**\nOrganizations should invest in remote infrastructure and flexible work policies."
        }
    ]
    
    # Add examples to the first prompt (Email Writing Assistant)
    email_prompt = next((p for p in existing_prompts if "Email" in p["task"]), None)
    if email_prompt:
        for example in additional_examples[:1]:  # Add first example to email prompt
            db.add_example(
                prompt_id=email_prompt["id"],
                input_text=example["input"],
                output_text=example["output"],
                critique="Excellent example - shows professional communication skills"
            )
    
    # Add examples to the second prompt (Code Review Assistant)
    code_prompt = next((p for p in existing_prompts if "Code" in p["task"]), None)
    if code_prompt:
        for example in additional_examples[1:2]:  # Add second example to code prompt
            db.add_example(
                prompt_id=code_prompt["id"],
                input_text=example["input"],
                output_text=example["output"],
                critique="Critical security example - demonstrates vulnerability identification"
            )
    
    # Add examples to the third prompt (Content Summarizer)
    summary_prompt = next((p for p in existing_prompts if "Content" in p["task"]), None)
    if summary_prompt:
        for example in additional_examples[2:3]:  # Add third example to summary prompt
            db.add_example(
                prompt_id=summary_prompt["id"],
                input_text=example["input"],
                output_text=example["output"],
                critique="Good summary - captures key points concisely"
            )
    
    print("✅ Added performance data and additional training examples!")

def verify_test_data():
    """Verify that test data was created correctly."""
    
    db = PromptDB()
    
    print("🔍 Verifying test data...")
    
    # Check prompts
    prompts = db.get_all_prompts()
    print(f"📊 Total prompts: {len(prompts)}")
    
    # Check lineages
    lineages = set(p["lineage_id"] for p in prompts)
    print(f"📈 Unique lineages: {len(lineages)}")
    
    # Check training data
    total_examples = 0
    for prompt in prompts:
        if prompt.get("training_data"):
            try:
                training_data = json.loads(prompt["training_data"])
                total_examples += len(training_data)
            except:
                pass
    
    print(f"🎯 Total training examples: {total_examples}")
    
    # Check database examples
    with db.session_scope() as session:
        db_examples = session.query(Example).count()
        print(f"💾 Database examples: {db_examples}")
    
    # Show sample prompt
    if prompts:
        sample = prompts[0]
        print(f"\n📝 Sample prompt: {sample['task']} (v{sample['version']})")
        print(f"   ID: {sample['id']}")
        print(f"   Lineage: {sample['lineage_id']}")
        
        # Handle training data properly
        training_count = 0
        if sample.get('training_data'):
            try:
                if isinstance(sample['training_data'], str):
                    training_data = json.loads(sample['training_data'])
                else:
                    training_data = sample['training_data']
                training_count = len(training_data) if isinstance(training_data, list) else 0
            except (json.JSONDecodeError, TypeError):
                training_count = 0
        print(f"   Training examples: {training_count}")
    
    print("✅ Test data verification complete!")

if __name__ == "__main__":
    print("🚀 Prompt Platform Test Data Generator")
    print("=" * 50)
    
    try:
        # Create test prompts
        create_test_prompts()
        
        # Add performance data
        create_performance_data()
        
        # Verify the data
        verify_test_data()
        
        print("\n🎉 Test data generation completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the Streamlit app: streamlit run prompt_platform/streamlit_app.py")
        print("2. Go to the '📋 Manage' tab to see the test prompts")
        print("3. Test the '✨ Improve' functionality with DSPy optimization")
        print("4. Try the '🧪 Test' feature with the training examples")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc() 