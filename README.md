# verbose-octo-carnival

11/10/23 - added 001-installing-workday-paystubs.py
The script uses Selenium and other libraries in Python to automate the process of logging into a Workday portal, navigating to the "My Payslips" section, and downloading paystubs as PDFs. It reads login credentials from a JSON file, interacts with web elements, and utilizes keypress simulwations to trigger the download of PDFs. The script also extracts and prints data from a table on the webpage. Note: Some parts of the script are commented out, and there are explanations and debug prints throughout. The primary goal seems to be automating the extraction and download of paystub information from a Workday portal.

11/19/23
Added 002_linkedin_easy_apply.py
LinkedIn Job Search Automation Project Summary
Project Overview
Objective: Automate the job searching and application process on LinkedIn using Python with Selenium.
Tools Used: Python, Selenium, ChromeDriver, JSON for credential storage, Miro for project planning.
High-Level Architecture
Job Search Platform: LinkedIn
Automation Script: Python with Selenium
WebDriver: ChromeDriver
Job Listing Data Storage: SQLite
Resume and Cover Letter Management: Manual handling or document management system
Logging and Monitoring: Implementing a logging system
Milestones and Learnings
Learning Selenium Basics: Explored Selenium for web automation, including interacting with web elements, clicking buttons, and filling forms.
Initial Setup: Created a LinkedIn bot using Selenium, logging in and navigating to the job search page.
Initial Job Scraping: Successfully scraped job details from job listings.
Security Verification Handling: Implemented a workaround for security verification checks.
Exception Handling: Implemented try-catch statements for better error handling during script execution.
Applying to Jobs: Successfully automated the Easy Apply process for job applications on over 400 jobs.
Dynamic Page Handling: Managed dynamic pages, handling diverse flows during the application process.
Challenges and Solutions
Security Verification: Overcame security verification challenges by implementing wait strategies.
Modal Handling: Implemented a method to handle and dismiss the "Save Application" modal.
Language Edge Case: Addressed an edge case with a job posting in Spanish.
Additional Questions Handling: Dynamically scraped and stored additional questions for reuse in future applications.
Script Optimization: Improved script efficiency by handling page timeouts and skipping unnecessary pages.
Key Features
Automated Easy Apply: Applied to over 400 jobs using Easy Apply automation.
Dynamic Page Navigation: Implemented dynamic navigation through diverse application flows.
Additional Questions Scraping: Dynamically scraped and stored additional questions for future use.
Script Optimization and Efficiency: Handled timeouts, skipped unnecessary pages, and improved overall script efficiency.
Future Enhancements
Framework Development: Consider building a framework for better code organization and scalability.
Resume and Cover Letter Automation: Explore options for automating the upload of resumes and cover letters.
Conclusion
The project successfully automated the job application process on LinkedIn, demonstrating effective use of Selenium for web automation. Ongoing enhancements and optimizations are planned for future iterations.

12/01/23
Added 003_linkedIn_framework.py
Were I basically made it more robust and maintainable than 002_linkedin_easy_apply.py. It's able to keep applying selective jobs. Using IPython, I can combine manual and automation to work as effecienity as I can since Ipython doesn't closes out when errors. Avoid verification. And I can manually submit what roles and answer addtional questions as needed. Applying to over 100 jobs in 30 minutes at best, which is not bad. With that in the pipeline, I can focus on other future projects while applying to jobs. And with what I learned so far, I can continue automating website tasks as I see fit for my day to day work. :D

Check out my https://oscar-leung.netlify.app/ portfolio if you read this far
