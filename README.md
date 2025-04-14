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


01/30/25
keywords
source venv/bin/activate
ipython

02/19/25
linkedin global search
("QA Engineer" OR "Quality Assurance" OR "SQA" OR "Software Engineer" OR "Automation Engineer" OR "Software Tester" OR "Test Engineer" OR "QA Automation" OR "Test Automation" OR "Front-End Developer" OR "React Developer" OR "Angular Developer" OR "Web Developer" OR "Mobile Developer" OR "UI Developer" OR "UX Developer" OR "Full-Stack Developer" OR "Test Lead" OR "Software Development Engineer in Test" OR "SDET")  
OR  
("Salesforce" OR "Jira" OR "Selenium" OR "Java" OR "Python" OR "TestRail" OR "Expresso" OR "SQL" OR "GitHub" OR "Jenkins" OR "TeamCity" OR "Automation Framework" OR "Regression Testing" OR "Unit Testing" OR "Smoke Testing" OR "Exploratory Testing" OR "Angular" OR "React" OR "Vue.js" OR "Node.js" OR "HTML" OR "CSS" OR "JavaScript" OR "TypeScript" OR "Swift" OR "Kotlin" OR "Android" OR "iOS" OR "Flutter" OR "Vue" OR "Redux" OR "Firebase" OR "Copado" OR "CI/CD" OR "DevOps" OR "TestNG" OR "Appium" OR "Figma")

("QA Engineer" OR "Quality Assurance" OR "SQA" OR "Software Engineer" OR "Automation Engineer" OR "Software Tester" OR "Test Engineer" OR "QA Automation" OR "Test Automation" OR "Front-End Developer" OR "React Developer" OR "Angular Developer" OR "Web Developer" OR "Mobile Developer" OR "UI Developer" OR "UX Developer" OR "Full-Stack Developer" OR "Test Lead" OR "Software Development Engineer in Test" OR "SDET" OR "Machine Learning Engineer" OR "AI Engineer" OR "Data Scientist")  
OR
("Salesforce" OR "Jira" OR "Selenium" OR "Java" OR "Python" OR "TestRail" OR "Expresso" OR "SQL" OR "GitHub" OR "Jenkins" OR "TeamCity" OR "Automation Framework" OR "Regression Testing" OR "Unit Testing" OR "Smoke Testing" OR "Exploratory Testing" OR "Angular" OR "React" OR "Vue.js" OR "Node.js" OR "HTML" OR "CSS" OR "JavaScript" OR "TypeScript" OR "Swift" OR "Kotlin" OR "Android" OR "iOS" OR "Flutter" OR "Vue" OR "Redux" OR "Firebase" OR "Copado" OR "CI/CD" OR "DevOps" OR "TestNG" OR "Appium" OR "Figma" OR "TensorFlow" OR "PyTorch" OR "Scikit-learn" OR "Keras" OR "OpenCV" OR "Pandas" OR "NumPy" OR "Matplotlib" OR "SciPy" OR "Hugging Face")  


("Quality Assurance Engineer" OR "QA Engineer" OR "Software Test Engineer" OR "Software Quality Assurance Engineer" OR "Software QA Engineer" OR "SDET" OR "Software Development Engineer in Test" OR "Software Engineer in Test" OR "Software Developer in Test" OR "Test Engineer" OR "Software Engineer")  
OR  
("Quality Assurance" OR "Java" OR "Testing" OR "Software Quality Assurance" OR "Selenium" OR "Selenium WebDriver" OR "Manual Testing" OR "Regression Testing" OR "Test Cases" OR "Functional Testing" OR "Black Box Testing" OR "Mobile Testing" OR "QA Engineering")  

("QA Engineer") OR
("Quality Assurance") OR
("SQA") OR
("Software Engineer") OR
("Automation Engineer") OR
("Software Tester") OR
("Test Engineer") OR
("QA Automation") OR
("Test Automation") OR
("Front-End Developer") OR
("React Developer") OR
("Angular Developer") OR
("Web Developer") OR
("Mobile Developer") OR
("UI Developer") OR
("UX Developer") OR
("Full-Stack Developer") OR
("Test Lead") OR
("Software Development Engineer in Test") OR
("SDET") OR
("Machine Learning Engineer") OR
("AI Engineer") OR
("Data Scientist") OR
("Cloud Engineer") OR
("DevOps Engineer") OR
("Cybersecurity Specialist") OR
("Data Analyst") OR
("Product Manager") OR
("Blockchain Developer") OR
("Salesforce") OR
("Jira") OR
("Selenium") OR
("Java") OR
("Python") OR
("TestRail") OR
("Espresso") OR
("SQL") OR
("GitHub") OR
("Jenkins") OR
("TeamCity") OR
("Automation Framework") OR
("Regression Testing") OR
("Unit Testing") OR
("Smoke Testing") OR
("Exploratory Testing") OR
("Angular") OR
("React") OR
("Vue.js") OR
("Node.js") OR
("HTML") OR
("CSS") OR
("JavaScript") OR
("TypeScript") OR
("Swift") OR
("Kotlin") OR
("Android") OR
("iOS") OR
("Flutter") OR
("Redux") OR
("Firebase") OR
("Copado") OR
("CI/CD") OR
("DevOps") OR
("TestNG") OR
("Appium") OR
("Figma") OR
("TensorFlow") OR
("PyTorch") OR
("OpenCV") OR
("Pandas") OR
("NumPy") OR
("Matplotlib") OR
("SciPy") OR
("Hugging Face") OR
("AWS") OR
("Azure") OR
("Google Cloud") OR
("Docker") OR
("Kubernetes") OR
("Microservices") OR
("GraphQL") OR
("Django") OR
("Flask") OR
("Spring Boot") OR
("Rust") OR
("Go") OR
("Ruby") OR
("PHP") OR
("Perl") OR
("Scala") OR
("SwiftUI") OR
("AR/VR") OR
("Unity") OR
("Unreal Engine") OR
("Blockchain") OR
("Solidity") OR
("Smart Contracts") OR
("RPA") OR
("Robotic Process Automation") OR
("Big Data") OR
("Hadoop") OR
("Spark") OR
("Kafka") OR
("ElasticSearch") OR
("Data Mining") OR
("Data Warehousing") OR
("Business Intelligence") OR
("ETL") OR
("Airflow") OR
("Tableau") OR
("Power BI") OR
("Snowflake") OR
("Redshift") OR
("Looker") OR
("Agile") OR
("Scrum") OR
("Kanban") OR
("Project Management") OR
("Leadership") OR
("Communication") OR
("Problem-Solving") OR
("Critical Thinking") OR
("Collaboration") OR
("Adaptability") OR
("Creativity") OR
("Time Management")


03/21/2025
(("QA Engineer") OR ("Quality Assurance") OR ("SQA") OR ("Software Engineer") OR ("Automation Engineer") OR ("Software Tester") OR ("Test Engineer") OR ("QA Automation") OR ("Test Automation") OR ("Front-End Developer") OR ("React Developer") OR ("Angular Developer") OR ("Web Developer") OR ("Mobile Developer") OR ("UI Developer") OR ("UX Developer") OR ("Full-Stack Developer") OR ("Software Development Engineer in Test") OR ("SDET") OR ("Machine Learning Engineer") OR ("AI Engineer") OR ("Data Scientist") OR ("Cloud Engineer") OR ("DevOps Engineer") OR ("Cybersecurity Specialist") OR ("Data Analyst") OR ("Product Manager") OR ("Blockchain Developer") OR ("Salesforce") OR ("Jira") OR ("Selenium") OR ("Java") OR ("Python") OR ("TestRail") OR ("Espresso") OR ("SQL") OR ("GitHub") OR ("Jenkins") OR ("TeamCity") OR ("Automation Framework") OR ("Regression Testing") OR ("Unit Testing") OR ("Smoke Testing") OR ("Exploratory Testing") OR ("Angular") OR ("React") OR ("Vue.js") OR ("Node.js") OR ("HTML") OR ("CSS") OR ("JavaScript") OR ("TypeScript") OR ("Swift") OR ("Kotlin") OR ("Android") OR ("iOS") OR ("Flutter") OR ("Redux") OR ("Firebase") OR ("Copado") OR ("CI/CD") OR ("DevOps") OR ("TestNG") OR ("Appium") OR ("Figma") OR ("TensorFlow") OR ("PyTorch") OR ("OpenCV") OR ("Pandas") OR ("NumPy") OR ("Matplotlib") OR ("SciPy") OR ("Hugging Face") OR ("AWS") OR ("Azure") OR ("Google Cloud") OR ("Docker") OR ("Kubernetes") OR ("Microservices") OR ("GraphQL") OR ("Django") OR ("Flask") OR ("Spring Boot") OR ("Rust") OR ("Go") OR ("Ruby") OR ("PHP") OR ("Perl") OR ("Scala") OR ("SwiftUI") OR ("AR/VR") OR ("Unity") OR ("Unreal Engine") OR ("Blockchain") OR ("Solidity") OR ("Smart Contracts") OR ("RPA") OR ("Robotic Process Automation") OR ("Big Data") OR ("Hadoop") OR ("Spark") OR ("Kafka") OR ("ElasticSearch") OR ("Data Mining") OR ("Data Warehousing") OR ("Business Intelligence") OR ("ETL") OR ("Airflow") OR ("Tableau") OR ("Power BI") OR ("Snowflake") OR ("Redshift") OR ("Looker") OR ("Agile") OR ("Scrum") OR ("Kanban") OR ("Project Management") OR ("Leadership") OR ("Communication") OR ("Problem-Solving") OR ("Critical Thinking") OR ("Collaboration") OR ("Adaptability") OR ("Creativity") OR ("Time Management"))
AND NOT ("Manager") AND NOT ("Engineering Manager") AND NOT ("Senior Manager") 
AND NOT ("Lead") AND NOT ("Principal") AND NOT ("Consultant")
