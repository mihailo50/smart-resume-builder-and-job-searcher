"""
Django management command to generate PDF previews and thumbnails for all templates.

This command:
1. Generates PDF previews from HTML templates using sample resume data
2. Generates PNG thumbnails from the PDFs
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from config.services.resume_pdf_generator import PremiumResumePDFGenerator

# Realistic resume personas for high-conversion thumbnails
RESUME_PERSONAS = {
    'modern-indigo': {
        'personal_info': {
            'full_name': 'Sarah Chen',
            'email': 'sarah.chen@email.com',
            'phone': '+1 (415) 555-0123',
            'location': 'San Francisco, CA',
            'linkedin_url': 'https://linkedin.com/in/sarahchen',
            'github_url': 'https://github.com/sarahchen',
            'portfolio_url': 'https://sarahchen.dev',
        },
        'summary': 'Senior Full-Stack Engineer with 6+ years building scalable web applications and leading cross-functional teams. Expert in React, Node.js, and cloud infrastructure. Delivered products serving 2M+ users with 99.9% uptime.',
        'title': 'Senior Full-Stack Engineer',
        'experiences': [
            {
                'title': 'Senior Full-Stack Engineer',
                'company': 'Stripe',
                'location': 'San Francisco, CA',
                'start_date': '2021-03',
                'end_date': None,
                'current': True,
                'description': '• Architected payment processing system handling $50B+ annually\n• Led team of 8 engineers, reducing API latency by 45%\n• Scaled microservices to 2M+ daily transactions',
                'order': 0,
            },
            {
                'title': 'Full-Stack Engineer',
                'company': 'Airbnb',
                'location': 'San Francisco, CA',
                'start_date': '2019-06',
                'end_date': '2021-02',
                'current': False,
                'description': '• Built booking platform features used by 150M+ users\n• Optimized database queries, improving page load by 60%\n• Implemented real-time notifications with WebSockets',
                'order': 1,
            },
            {
                'title': 'Software Engineer',
                'company': 'Uber',
                'location': 'San Francisco, CA',
                'start_date': '2018-01',
                'end_date': '2019-05',
                'current': False,
                'description': '• Developed driver matching algorithms reducing wait time by 30%\n• Built React components for mobile web platform',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'B.S. Computer Science',
                'institution': 'Stanford University',
                'institution': 'Stanford University',
                'school': 'Stanford University',
                'location': 'Stanford, CA',
                'start_date': '2014-09',
                'end_date': '2018-06',
                'current': False,
                'description': 'Magna Cum Laude, GPA: 3.9/4.0',
                'order': 0,
            },
        ],
        'skills': [
            {'name': 'React', 'level': 'Expert', 'category': 'Frontend', 'order': 0},
            {'name': 'Node.js', 'level': 'Expert', 'category': 'Backend', 'order': 1},
            {'name': 'TypeScript', 'level': 'Expert', 'category': 'Languages', 'order': 2},
            {'name': 'AWS', 'level': 'Advanced', 'category': 'Cloud', 'order': 3},
            {'name': 'PostgreSQL', 'level': 'Advanced', 'category': 'Database', 'order': 4},
            {'name': 'Docker', 'level': 'Advanced', 'category': 'DevOps', 'order': 5},
            {'name': 'Kubernetes', 'level': 'Intermediate', 'category': 'DevOps', 'order': 6},
            {'name': 'GraphQL', 'level': 'Advanced', 'category': 'API', 'order': 7},
            {'name': 'Redis', 'level': 'Intermediate', 'category': 'Database', 'order': 8},
        ],
        'projects': [
            {
                'name': 'Real-Time Analytics Dashboard',
                'title': 'Real-Time Analytics Dashboard',
                'description': 'Built analytics platform processing 10M+ events/day with sub-100ms query latency. Used React, D3.js, and WebSocket connections.',
                'technologies': 'React, Node.js, PostgreSQL, Redis, WebSockets',
                'start_date': '2022-01',
                'end_date': '2022-06',
                'order': 0,
            },
            {
                'name': 'Microservices Architecture',
                'title': 'Microservices Architecture',
                'description': 'Designed and implemented microservices platform reducing deployment time by 70%. Containerized with Docker and orchestrated with Kubernetes.',
                'technologies': 'Docker, Kubernetes, AWS, Terraform',
                'start_date': '2021-08',
                'end_date': '2022-03',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'AWS Certified Solutions Architect',
                'title': 'AWS Certified Solutions Architect',
                'issuer': 'Amazon Web Services',
                'issue_date': '2020-05',
                'expiry_date': None,
                'order': 0,
            },
            {
                'name': 'Google Cloud Professional Architect',
                'title': 'Google Cloud Professional Architect',
                'issuer': 'Google Cloud',
                'issue_date': '2021-11',
                'expiry_date': '2024-11',
                'order': 1,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'Mandarin', 'proficiency': 'Fluent', 'order': 1},
        ],
        'interests': [
            {'name': 'Open Source', 'order': 0},
            {'name': 'Tech Blogging', 'order': 1},
            {'name': 'Rock Climbing', 'order': 2},
        ],
    },
    'sidebar-teal': {
        'personal_info': {
            'full_name': 'Marcus Rodriguez',
            'email': 'marcus.rodriguez@email.com',
            'phone': '+1 (202) 555-0145',
            'location': 'Washington, DC',
            'linkedin_url': 'https://linkedin.com/in/marcusrodriguez',
            'github_url': 'https://github.com/marcusrodriguez',
            'portfolio_url': 'https://marcusrodriguez.tech',
        },
        'summary': 'Cybersecurity Analyst with 5+ years protecting enterprise infrastructure from advanced threats. Expert in penetration testing, threat intelligence, and security architecture. Secured systems handling $1B+ in transactions.',
        'title': 'Senior Cybersecurity Analyst',
        'experiences': [
            {
                'title': 'Senior Cybersecurity Analyst',
                'company': 'CrowdStrike',
                'location': 'Arlington, VA',
                'start_date': '2020-08',
                'end_date': None,
                'current': True,
                'description': '• Detected and mitigated 500+ security incidents, preventing $2M+ in potential losses\n• Led security audits for Fortune 500 clients\n• Reduced mean time to detection by 65%',
                'order': 0,
            },
            {
                'title': 'Cybersecurity Specialist',
                'company': 'Mandiant',
                'location': 'Alexandria, VA',
                'start_date': '2019-01',
                'end_date': '2020-07',
                'current': False,
                'description': '• Conducted 200+ penetration tests for financial institutions\n• Developed automated threat detection scripts, improving efficiency by 50%',
                'order': 1,
            },
            {
                'title': 'Security Engineer',
                'company': 'Booz Allen Hamilton',
                'location': 'McLean, VA',
                'start_date': '2018-06',
                'end_date': '2018-12',
                'current': False,
                'description': '• Implemented SIEM solutions monitoring 10K+ endpoints\n• Created security training programs for 500+ employees',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'M.S. Cybersecurity',
                'institution': 'George Washington University',
                'school': 'George Washington University',
                'location': 'Washington, DC',
                'start_date': '2016-09',
                'end_date': '2018-05',
                'current': False,
                'description': 'Summa Cum Laude, GPA: 3.95/4.0',
                'order': 0,
            },
            {
                'degree': 'B.S. Computer Science',
                'institution': 'Virginia Tech',
                'school': 'Virginia Tech',
                'location': 'Blacksburg, VA',
                'start_date': '2012-09',
                'end_date': '2016-05',
                'current': False,
                'description': 'Magna Cum Laude',
                'order': 1,
            },
        ],
        'skills': [
            {'name': 'Penetration Testing', 'level': 'Expert', 'category': 'Security', 'order': 0},
            {'name': 'SIEM', 'level': 'Expert', 'category': 'Security', 'order': 1},
            {'name': 'Python', 'level': 'Advanced', 'category': 'Programming', 'order': 2},
            {'name': 'Splunk', 'level': 'Expert', 'category': 'Tools', 'order': 3},
            {'name': 'Wireshark', 'level': 'Advanced', 'category': 'Tools', 'order': 4},
            {'name': 'Metasploit', 'level': 'Advanced', 'category': 'Tools', 'order': 5},
            {'name': 'Burp Suite', 'level': 'Expert', 'category': 'Tools', 'order': 6},
            {'name': 'AWS Security', 'level': 'Advanced', 'category': 'Cloud', 'order': 7},
            {'name': 'Kubernetes Security', 'level': 'Intermediate', 'category': 'DevOps', 'order': 8},
        ],
        'projects': [
            {
                'name': 'Threat Intelligence Platform',
                'title': 'Threat Intelligence Platform',
                'description': 'Built automated threat intelligence system aggregating data from 50+ sources. Reduced threat detection time by 80%.',
                'technologies': 'Python, Elasticsearch, Kafka, React',
                'start_date': '2021-03',
                'end_date': '2021-09',
                'order': 0,
            },
            {
                'name': 'Security Automation Framework',
                'title': 'Security Automation Framework',
                'description': 'Developed framework automating security scans and vulnerability assessments. Saved 20 hours/week in manual work.',
                'technologies': 'Python, Ansible, Docker, Jenkins',
                'start_date': '2020-11',
                'end_date': '2021-05',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'CISSP',
                'title': 'CISSP',
                'issuer': 'ISC²',
                'issue_date': '2019-08',
                'expiry_date': None,
                'order': 0,
            },
            {
                'name': 'CEH',
                'title': 'CEH',
                'issuer': 'EC-Council',
                'issue_date': '2018-12',
                'expiry_date': None,
                'order': 1,
            },
            {
                'name': 'AWS Security Specialty',
                'title': 'AWS Security Specialty',
                'issuer': 'Amazon Web Services',
                'issue_date': '2021-04',
                'expiry_date': '2024-04',
                'order': 2,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'Spanish', 'proficiency': 'Fluent', 'order': 1},
        ],
        'interests': [
            {'name': 'Bug Bounty Hunting', 'order': 0},
            {'name': 'Cybersecurity Research', 'order': 1},
        ],
    },
    'creative-violet': {
        'personal_info': {
            'full_name': 'Emma Thompson',
            'email': 'emma.thompson@email.com',
            'phone': '+1 (310) 555-0198',
            'location': 'Los Angeles, CA',
            'linkedin_url': 'https://linkedin.com/in/emmathompson',
            'github_url': 'https://github.com/emmathompson',
            'portfolio_url': 'https://emmathompson.design',
        },
        'summary': 'Product Designer with 6+ years creating intuitive, user-centered experiences for mobile and web. Led design for products with 5M+ users. Expert in design systems, prototyping, and user research.',
        'title': 'Senior Product Designer',
        'experiences': [
            {
                'title': 'Senior Product Designer',
                'company': 'Figma',
                'location': 'San Francisco, CA',
                'start_date': '2021-01',
                'end_date': None,
                'current': True,
                'description': '• Designed core features used by 4M+ designers worldwide\n• Led design system migration, improving consistency by 90%\n• Conducted user research with 200+ participants',
                'order': 0,
            },
            {
                'title': 'Product Designer',
                'company': 'Adobe',
                'location': 'San Jose, CA',
                'start_date': '2019-03',
                'end_date': '2020-12',
                'current': False,
                'description': '• Redesigned mobile app, increasing user engagement by 45%\n• Created design system components used across 10+ products',
                'order': 1,
            },
            {
                'title': 'UI/UX Designer',
                'company': 'Shopify',
                'location': 'Ottawa, ON',
                'start_date': '2017-06',
                'end_date': '2019-02',
                'current': False,
                'description': '• Designed e-commerce templates generating $500K+ in revenue\n• Improved checkout conversion rate by 35%',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'B.F.A. Graphic Design',
                'institution': 'Art Center College of Design',
                'school': 'Art Center College of Design',
                'location': 'Pasadena, CA',
                'start_date': '2013-09',
                'end_date': '2017-05',
                'current': False,
                'description': 'Summa Cum Laude',
                'order': 0,
            },
        ],
        'skills': [
            {'name': 'Figma', 'level': 'Expert', 'category': 'Design Tools', 'order': 0},
            {'name': 'Sketch', 'level': 'Expert', 'category': 'Design Tools', 'order': 1},
            {'name': 'Adobe Creative Suite', 'level': 'Expert', 'category': 'Design Tools', 'order': 2},
            {'name': 'Prototyping', 'level': 'Expert', 'category': 'Skills', 'order': 3},
            {'name': 'User Research', 'level': 'Advanced', 'category': 'Skills', 'order': 4},
            {'name': 'Design Systems', 'level': 'Expert', 'category': 'Skills', 'order': 5},
            {'name': 'HTML/CSS', 'level': 'Intermediate', 'category': 'Development', 'order': 6},
            {'name': 'React', 'level': 'Basic', 'category': 'Development', 'order': 7},
        ],
        'projects': [
            {
                'name': 'Design System Library',
                'title': 'Design System Library',
                'description': 'Created comprehensive design system with 200+ components. Adopted by 15+ product teams, reducing design time by 60%.',
                'technologies': 'Figma, React, Storybook',
                'start_date': '2021-06',
                'end_date': '2022-02',
                'order': 0,
            },
            {
                'name': 'Mobile App Redesign',
                'title': 'Mobile App Redesign',
                'description': 'Redesigned mobile app interface, increasing daily active users by 50% and improving App Store rating from 3.8 to 4.7.',
                'technologies': 'Figma, Principle, After Effects',
                'start_date': '2020-05',
                'end_date': '2020-11',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'Google UX Design Certificate',
                'title': 'Google UX Design Certificate',
                'issuer': 'Google',
                'issue_date': '2020-09',
                'expiry_date': None,
                'order': 0,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'French', 'proficiency': 'Conversational', 'order': 1},
        ],
        'interests': [
            {'name': 'Typography', 'order': 0},
            {'name': 'Photography', 'order': 1},
            {'name': 'Art Exhibitions', 'order': 2},
        ],
    },
    'ats-classic': {
        'personal_info': {
            'full_name': 'James Park',
            'email': 'james.park@email.com',
            'phone': '+1 (206) 555-0167',
            'location': 'Seattle, WA',
            'linkedin_url': 'https://linkedin.com/in/jamespark',
            'github_url': 'https://github.com/jamespark',
            'portfolio_url': 'https://jamespark.dev',
        },
        'summary': 'Junior Backend Developer with 2+ years building scalable APIs and microservices. Strong foundation in Python, Django, and cloud technologies. Passionate about clean code and best practices.',
        'title': 'Backend Developer',
        'experiences': [
            {
                'title': 'Backend Developer',
                'company': 'Microsoft',
                'location': 'Redmond, WA',
                'start_date': '2022-07',
                'end_date': None,
                'current': True,
                'description': '• Developed REST APIs serving 1M+ requests/day\n• Optimized database queries, reducing response time by 40%\n• Wrote unit tests achieving 85% code coverage',
                'order': 0,
            },
            {
                'title': 'Software Engineering Intern',
                'company': 'Amazon',
                'location': 'Seattle, WA',
                'start_date': '2021-06',
                'end_date': '2021-08',
                'current': False,
                'description': '• Built internal tooling reducing manual work by 30 hours/week\n• Participated in code reviews and agile ceremonies',
                'order': 1,
            },
        ],
        'educations': [
            {
                'degree': 'B.S. Computer Science',
                'institution': 'University of Washington',
                'school': 'University of Washington',
                'location': 'Seattle, WA',
                'start_date': '2018-09',
                'end_date': '2022-06',
                'current': False,
                'description': 'Dean\'s List, GPA: 3.7/4.0',
                'order': 0,
            },
        ],
        'skills': [
            {'name': 'Python', 'level': 'Advanced', 'category': 'Languages', 'order': 0},
            {'name': 'Django', 'level': 'Advanced', 'category': 'Frameworks', 'order': 1},
            {'name': 'PostgreSQL', 'level': 'Intermediate', 'category': 'Database', 'order': 2},
            {'name': 'Redis', 'level': 'Intermediate', 'category': 'Database', 'order': 3},
            {'name': 'Docker', 'level': 'Intermediate', 'category': 'DevOps', 'order': 4},
            {'name': 'AWS', 'level': 'Basic', 'category': 'Cloud', 'order': 5},
            {'name': 'Git', 'level': 'Advanced', 'category': 'Tools', 'order': 6},
            {'name': 'REST APIs', 'level': 'Advanced', 'category': 'Skills', 'order': 7},
        ],
        'projects': [
            {
                'name': 'E-Commerce API',
                'title': 'E-Commerce API',
                'description': 'Built RESTful API for e-commerce platform with authentication, payment processing, and order management. Handles 10K+ requests/day.',
                'technologies': 'Django, PostgreSQL, Redis, Stripe API',
                'start_date': '2021-09',
                'end_date': '2022-04',
                'order': 0,
            },
            {
                'name': 'Task Management System',
                'title': 'Task Management System',
                'description': 'Developed task management API with real-time updates using WebSockets. Supports teams of up to 100 users.',
                'technologies': 'Django, PostgreSQL, WebSockets, Docker',
                'start_date': '2020-12',
                'end_date': '2021-05',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'AWS Certified Cloud Practitioner',
                'title': 'AWS Certified Cloud Practitioner',
                'issuer': 'Amazon Web Services',
                'issue_date': '2022-03',
                'expiry_date': '2025-03',
                'order': 0,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'Korean', 'proficiency': 'Fluent', 'order': 1},
        ],
        'interests': [
            {'name': 'Open Source', 'order': 0},
            {'name': 'Tech Meetups', 'order': 1},
        ],
    },
    'executive-gold': {
        'personal_info': {
            'full_name': 'David Kim',
            'email': 'david.kim@email.com',
            'phone': '+1 (650) 555-0189',
            'location': 'Palo Alto, CA',
            'linkedin_url': 'https://linkedin.com/in/davidkim',
            'github_url': 'https://github.com/davidkim',
            'portfolio_url': 'https://davidkim.tech',
        },
        'summary': 'Tech Lead and Engineering Manager with 10+ years leading high-performing engineering teams. Delivered products generating $100M+ in revenue. Expert in system architecture, team building, and technical strategy.',
        'title': 'Engineering Manager',
        'experiences': [
            {
                'title': 'Engineering Manager',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'start_date': '2020-04',
                'end_date': None,
                'current': True,
                'description': '• Lead team of 12 engineers building cloud infrastructure products\n• Increased team velocity by 60% through process improvements\n• Delivered products generating $50M+ in annual revenue',
                'order': 0,
            },
            {
                'title': 'Senior Tech Lead',
                'company': 'Meta',
                'location': 'Menlo Park, CA',
                'start_date': '2017-08',
                'end_date': '2020-03',
                'current': False,
                'description': '• Architected systems serving 500M+ users\n• Mentored 15+ engineers, 8 promoted to senior roles\n• Reduced infrastructure costs by $5M annually',
                'order': 1,
            },
            {
                'title': 'Senior Software Engineer',
                'company': 'LinkedIn',
                'location': 'Sunnyvale, CA',
                'start_date': '2014-01',
                'end_date': '2017-07',
                'current': False,
                'description': '• Built recommendation engine improving engagement by 40%\n• Led migration to microservices architecture',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'M.S. Computer Science',
                'institution': 'Carnegie Mellon University',
                'school': 'Carnegie Mellon University',
                'location': 'Pittsburgh, PA',
                'start_date': '2011-09',
                'end_date': '2013-05',
                'current': False,
                'description': 'Thesis: Distributed Systems Optimization',
                'order': 0,
            },
            {
                'degree': 'B.S. Computer Science',
                'institution': 'UC Berkeley',
                'school': 'UC Berkeley',
                'location': 'Berkeley, CA',
                'start_date': '2007-09',
                'end_date': '2011-05',
                'current': False,
                'description': 'Magna Cum Laude',
                'order': 1,
            },
        ],
        'skills': [
            {'name': 'System Architecture', 'level': 'Expert', 'category': 'Engineering', 'order': 0},
            {'name': 'Team Leadership', 'level': 'Expert', 'category': 'Management', 'order': 1},
            {'name': 'Python', 'level': 'Expert', 'category': 'Languages', 'order': 2},
            {'name': 'Go', 'level': 'Advanced', 'category': 'Languages', 'order': 3},
            {'name': 'Kubernetes', 'level': 'Expert', 'category': 'DevOps', 'order': 4},
            {'name': 'AWS', 'level': 'Expert', 'category': 'Cloud', 'order': 5},
            {'name': 'Distributed Systems', 'level': 'Expert', 'category': 'Architecture', 'order': 6},
            {'name': 'Agile/Scrum', 'level': 'Expert', 'category': 'Methodology', 'order': 7},
        ],
        'projects': [
            {
                'name': 'Cloud Infrastructure Platform',
                'title': 'Cloud Infrastructure Platform',
                'description': 'Architected and led development of cloud platform serving 10K+ customers. Reduced deployment time by 80% and improved reliability to 99.99%.',
                'technologies': 'Kubernetes, Go, Python, AWS, Terraform',
                'start_date': '2020-06',
                'end_date': '2022-03',
                'order': 0,
            },
        ],
        'certifications': [
            {
                'name': 'AWS Certified Solutions Architect - Professional',
                'title': 'AWS Certified Solutions Architect - Professional',
                'issuer': 'Amazon Web Services',
                'issue_date': '2019-11',
                'expiry_date': None,
                'order': 0,
            },
            {
                'name': 'Google Cloud Professional Architect',
                'title': 'Google Cloud Professional Architect',
                'issuer': 'Google Cloud',
                'issue_date': '2020-08',
                'expiry_date': '2023-08',
                'order': 1,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'Korean', 'proficiency': 'Fluent', 'order': 1},
        ],
        'interests': [
            {'name': 'Tech Leadership', 'order': 0},
            {'name': 'Public Speaking', 'order': 1},
        ],
    },
    'tech-cyan': {
        'personal_info': {
            'full_name': 'Alex Morgan',
            'email': 'alex.morgan@email.com',
            'phone': '+1 (512) 555-0176',
            'location': 'Austin, TX',
            'linkedin_url': 'https://linkedin.com/in/alexmorgan',
            'github_url': 'https://github.com/alexmorgan',
            'portfolio_url': 'https://alexmorgan.dev',
        },
        'summary': 'DevOps Engineer with 5+ years automating infrastructure and optimizing CI/CD pipelines. Expert in Kubernetes, Terraform, and cloud-native technologies. Reduced deployment time by 90% and infrastructure costs by 40%.',
        'title': 'Senior DevOps Engineer',
        'experiences': [
            {
                'title': 'Senior DevOps Engineer',
                'company': 'Netflix',
                'location': 'Los Gatos, CA',
                'start_date': '2021-02',
                'end_date': None,
                'current': True,
                'description': '• Built Kubernetes platform serving 200M+ subscribers\n• Automated deployments reducing release time from 4 hours to 15 minutes\n• Reduced infrastructure costs by $8M annually',
                'order': 0,
            },
            {
                'title': 'DevOps Engineer',
                'company': 'Twilio',
                'location': 'San Francisco, CA',
                'start_date': '2019-05',
                'end_date': '2021-01',
                'current': False,
                'description': '• Implemented GitOps workflows improving deployment frequency by 5x\n• Built monitoring dashboards reducing incident response time by 50%',
                'order': 1,
            },
            {
                'title': 'Site Reliability Engineer',
                'company': 'Dropbox',
                'location': 'San Francisco, CA',
                'start_date': '2018-06',
                'end_date': '2019-04',
                'current': False,
                'description': '• Maintained 99.99% uptime for storage infrastructure\n• Automated incident response reducing MTTR by 60%',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'B.S. Computer Engineering',
                'institution': 'University of Texas at Austin',
                'school': 'University of Texas at Austin',
                'location': 'Austin, TX',
                'start_date': '2014-09',
                'end_date': '2018-05',
                'current': False,
                'description': 'Magna Cum Laude',
                'order': 0,
            },
        ],
        'skills': [
            {'name': 'Kubernetes', 'level': 'Expert', 'category': 'Orchestration', 'order': 0},
            {'name': 'Terraform', 'level': 'Expert', 'category': 'IaC', 'order': 1},
            {'name': 'Docker', 'level': 'Expert', 'category': 'Containers', 'order': 2},
            {'name': 'AWS', 'level': 'Expert', 'category': 'Cloud', 'order': 3},
            {'name': 'Jenkins', 'level': 'Advanced', 'category': 'CI/CD', 'order': 4},
            {'name': 'GitLab CI', 'level': 'Advanced', 'category': 'CI/CD', 'order': 5},
            {'name': 'Prometheus', 'level': 'Advanced', 'category': 'Monitoring', 'order': 6},
            {'name': 'Grafana', 'level': 'Advanced', 'category': 'Monitoring', 'order': 7},
            {'name': 'Ansible', 'level': 'Intermediate', 'category': 'Automation', 'order': 8},
        ],
        'projects': [
            {
                'name': 'Multi-Cloud Infrastructure',
                'title': 'Multi-Cloud Infrastructure',
                'description': 'Designed and implemented multi-cloud infrastructure using Kubernetes. Achieved 99.99% uptime across AWS, GCP, and Azure.',
                'technologies': 'Kubernetes, Terraform, AWS, GCP, Azure',
                'start_date': '2021-06',
                'end_date': '2022-04',
                'order': 0,
            },
            {
                'name': 'CI/CD Pipeline Automation',
                'title': 'CI/CD Pipeline Automation',
                'description': 'Built automated CI/CD pipeline reducing deployment time by 90%. Supports 500+ microservices with zero-downtime deployments.',
                'technologies': 'Jenkins, Kubernetes, Docker, Terraform',
                'start_date': '2020-08',
                'end_date': '2021-05',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'CKA - Certified Kubernetes Administrator',
                'title': 'CKA - Certified Kubernetes Administrator',
                'issuer': 'Cloud Native Computing Foundation',
                'issue_date': '2020-09',
                'expiry_date': '2023-09',
                'order': 0,
            },
            {
                'name': 'AWS Certified DevOps Engineer',
                'title': 'AWS Certified DevOps Engineer',
                'issuer': 'Amazon Web Services',
                'issue_date': '2021-03',
                'expiry_date': '2024-03',
                'order': 1,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
        ],
        'interests': [
            {'name': 'Infrastructure as Code', 'order': 0},
            {'name': 'Cloud Native Technologies', 'order': 1},
        ],
    },
    'elegant-emerald': {
        'personal_info': {
            'full_name': 'Priya Patel',
            'email': 'priya.patel@email.com',
            'phone': '+1 (617) 555-0134',
            'location': 'Boston, MA',
            'linkedin_url': 'https://linkedin.com/in/priyapatel',
            'github_url': 'https://github.com/priyapatel',
            'portfolio_url': 'https://priyapatel.tech',
        },
        'summary': 'Data Scientist with 6+ years turning complex data into actionable insights. Expert in machine learning, statistical modeling, and data visualization. Built models improving business metrics by 35% and reducing costs by $3M annually.',
        'title': 'Senior Data Scientist',
        'experiences': [
            {
                'title': 'Senior Data Scientist',
                'company': 'Spotify',
                'location': 'New York, NY',
                'start_date': '2020-09',
                'end_date': None,
                'current': True,
                'description': '• Built recommendation models serving 400M+ users, increasing engagement by 30%\n• Led team of 5 data scientists on personalization projects\n• Reduced churn rate by 25% through predictive modeling',
                'order': 0,
            },
            {
                'title': 'Data Scientist',
                'company': 'Airbnb',
                'location': 'San Francisco, CA',
                'start_date': '2018-11',
                'end_date': '2020-08',
                'current': False,
                'description': '• Developed pricing models increasing revenue by $50M annually\n• Built fraud detection system reducing false positives by 60%',
                'order': 1,
            },
            {
                'title': 'Data Analyst',
                'company': 'Uber',
                'location': 'San Francisco, CA',
                'start_date': '2017-06',
                'end_date': '2018-10',
                'current': False,
                'description': '• Analyzed ride patterns optimizing driver allocation\n• Created dashboards used by 500+ operations team members',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'M.S. Data Science',
                'institution': 'MIT',
                'school': 'MIT',
                'location': 'Cambridge, MA',
                'start_date': '2015-09',
                'end_date': '2017-05',
                'current': False,
                'description': 'Thesis: Deep Learning for Time Series Forecasting',
                'order': 0,
            },
            {
                'degree': 'B.S. Statistics',
                'institution': 'UC Berkeley',
                'school': 'UC Berkeley',
                'location': 'Berkeley, CA',
                'start_date': '2011-09',
                'end_date': '2015-05',
                'current': False,
                'description': 'Summa Cum Laude',
                'order': 1,
            },
        ],
        'skills': [
            {'name': 'Python', 'level': 'Expert', 'category': 'Languages', 'order': 0},
            {'name': 'R', 'level': 'Advanced', 'category': 'Languages', 'order': 1},
            {'name': 'SQL', 'level': 'Expert', 'category': 'Database', 'order': 2},
            {'name': 'Machine Learning', 'level': 'Expert', 'category': 'ML', 'order': 3},
            {'name': 'TensorFlow', 'level': 'Advanced', 'category': 'ML Frameworks', 'order': 4},
            {'name': 'PyTorch', 'level': 'Advanced', 'category': 'ML Frameworks', 'order': 5},
            {'name': 'Pandas', 'level': 'Expert', 'category': 'Libraries', 'order': 6},
            {'name': 'Tableau', 'level': 'Advanced', 'category': 'Visualization', 'order': 7},
            {'name': 'Spark', 'level': 'Intermediate', 'category': 'Big Data', 'order': 8},
        ],
        'projects': [
            {
                'name': 'Recommendation Engine',
                'title': 'Recommendation Engine',
                'description': 'Built deep learning recommendation system processing 1B+ interactions. Improved click-through rate by 35% and user engagement by 40%.',
                'technologies': 'Python, TensorFlow, Spark, Kubernetes',
                'start_date': '2021-01',
                'end_date': '2021-10',
                'order': 0,
            },
            {
                'name': 'Predictive Analytics Platform',
                'title': 'Predictive Analytics Platform',
                'description': 'Developed platform for real-time predictions serving 10M+ requests/day. Reduced prediction latency from 500ms to 50ms.',
                'technologies': 'Python, FastAPI, Redis, PostgreSQL',
                'start_date': '2020-03',
                'end_date': '2020-11',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'Google Cloud Professional Data Engineer',
                'title': 'Google Cloud Professional Data Engineer',
                'issuer': 'Google Cloud',
                'issue_date': '2021-07',
                'expiry_date': '2024-07',
                'order': 0,
            },
            {
                'name': 'AWS Certified Machine Learning Specialty',
                'title': 'AWS Certified Machine Learning Specialty',
                'issuer': 'Amazon Web Services',
                'issue_date': '2020-12',
                'expiry_date': '2023-12',
                'order': 1,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
            {'name': 'Hindi', 'proficiency': 'Fluent', 'order': 1},
        ],
        'interests': [
            {'name': 'Machine Learning Research', 'order': 0},
            {'name': 'Data Visualization', 'order': 1},
        ],
    },
    'minimalist-black': {
        'personal_info': {
            'full_name': 'Ryan Foster',
            'email': 'ryan.foster@email.com',
            'phone': '+1 (212) 555-0156',
            'location': 'New York, NY',
            'linkedin_url': 'https://linkedin.com/in/ryanfoster',
            'github_url': 'https://github.com/ryanfoster',
            'portfolio_url': 'https://ryanfoster.dev',
        },
        'summary': 'Frontend Engineer with 4+ years building responsive, performant web applications. Expert in React, TypeScript, and modern JavaScript. Delivered features used by 10M+ users with 99.9% uptime.',
        'title': 'Senior Frontend Engineer',
        'experiences': [
            {
                'title': 'Senior Frontend Engineer',
                'company': 'Shopify',
                'location': 'Ottawa, ON',
                'start_date': '2021-05',
                'end_date': None,
                'current': True,
                'description': '• Built React components used by 2M+ merchants\n• Optimized bundle size reducing load time by 50%\n• Led migration to TypeScript improving code quality',
                'order': 0,
            },
            {
                'title': 'Frontend Engineer',
                'company': 'Etsy',
                'location': 'Brooklyn, NY',
                'start_date': '2019-08',
                'end_date': '2021-04',
                'current': False,
                'description': '• Developed e-commerce features increasing conversion by 25%\n• Built design system components used across 50+ pages',
                'order': 1,
            },
            {
                'title': 'Frontend Developer',
                'company': 'Vimeo',
                'location': 'New York, NY',
                'start_date': '2018-06',
                'end_date': '2019-07',
                'current': False,
                'description': '• Built video player features used by 260M+ users\n• Improved accessibility score from 75 to 95',
                'order': 2,
            },
        ],
        'educations': [
            {
                'degree': 'B.S. Computer Science',
                'institution': 'NYU',
                'school': 'NYU',
                'location': 'New York, NY',
                'start_date': '2014-09',
                'end_date': '2018-05',
                'current': False,
                'description': 'Dean\'s List',
                'order': 0,
            },
        ],
        'skills': [
            {'name': 'React', 'level': 'Expert', 'category': 'Frameworks', 'order': 0},
            {'name': 'TypeScript', 'level': 'Expert', 'category': 'Languages', 'order': 1},
            {'name': 'JavaScript', 'level': 'Expert', 'category': 'Languages', 'order': 2},
            {'name': 'Next.js', 'level': 'Advanced', 'category': 'Frameworks', 'order': 3},
            {'name': 'CSS/SCSS', 'level': 'Expert', 'category': 'Styling', 'order': 4},
            {'name': 'GraphQL', 'level': 'Advanced', 'category': 'API', 'order': 5},
            {'name': 'Webpack', 'level': 'Intermediate', 'category': 'Build Tools', 'order': 6},
            {'name': 'Jest', 'level': 'Advanced', 'category': 'Testing', 'order': 7},
        ],
        'projects': [
            {
                'name': 'Component Library',
                'title': 'Component Library',
                'description': 'Created reusable component library with 100+ components. Used across 20+ products, reducing development time by 40%.',
                'technologies': 'React, TypeScript, Storybook, Styled Components',
                'start_date': '2021-09',
                'end_date': '2022-05',
                'order': 0,
            },
            {
                'name': 'Performance Optimization',
                'title': 'Performance Optimization',
                'description': 'Optimized web application performance, improving Lighthouse score from 65 to 95. Reduced bundle size by 40% and load time by 60%.',
                'technologies': 'React, Webpack, Code Splitting, Lazy Loading',
                'start_date': '2020-11',
                'end_date': '2021-04',
                'order': 1,
            },
        ],
        'certifications': [
            {
                'name': 'Meta Front-End Developer Certificate',
                'title': 'Meta Front-End Developer Certificate',
                'issuer': 'Meta',
                'issue_date': '2021-02',
                'expiry_date': None,
                'order': 0,
            },
        ],
        'languages': [
            {'name': 'English', 'proficiency': 'Native', 'order': 0},
        ],
        'interests': [
            {'name': 'Web Performance', 'order': 0},
            {'name': 'UI/UX Design', 'order': 1},
        ],
    },
}


class Command(BaseCommand):
    help = 'Generate PDF previews and thumbnails for all resume templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-pdfs',
            action='store_true',
            help='Skip PDF generation, only generate thumbnails from existing PDFs',
        )

    def handle(self, *args, **options):
        generator = PremiumResumePDFGenerator()
        
        # Set up directories
        media_root = Path(settings.MEDIA_ROOT)
        previews_dir = media_root / 'templates' / 'previews'
        thumbnails_dir = media_root / 'templates' / 'thumbnails'
        
        previews_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        template_ids = generator.AVAILABLE_TEMPLATES
        pdf_success = 0
        pdf_errors = 0
        
        # Step 1: Generate PDF previews
        if not options['skip_pdfs']:
            self.stdout.write('Generating PDF previews...')
            self.stdout.write('')
            
            for template_id in template_ids:
                pdf_path = previews_dir / f'resume_{template_id}.pdf'
                
                try:
                    self.stdout.write(f'Generating PDF for {template_id}...', ending=' ')
                    
                    # Get persona data for this template
                    persona_data = RESUME_PERSONAS.get(template_id, RESUME_PERSONAS['modern-indigo'])
                    
                    # Prepare resume data structure
                    resume_data = {
                        'personal_info': persona_data['personal_info'],
                        'summary': persona_data['summary'],
                        'title': persona_data.get('title', ''),
                        'experiences': persona_data['experiences'],
                        'educations': persona_data['educations'],
                        'skills': persona_data['skills'],
                        'projects': persona_data['projects'],
                        'certifications': persona_data['certifications'],
                        'languages': persona_data['languages'],
                        'interests': persona_data['interests'],
                    }
                    
                    # Generate PDF
                    pdf_bytes, _ = generator.generate_pdf(
                        resume_data=resume_data,
                        template_name=template_id,
                        font_combination='modern',
                        ats_mode=False,
                    )
                    
                    # Save PDF
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bytes)
                    
                    self.stdout.write(self.style.SUCCESS('OK'))
                    pdf_success += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))
                    pdf_errors += 1
        
        # Step 2: Generate thumbnails from PDFs
        self.stdout.write('')
        self.stdout.write('Generating thumbnails from PDFs...')
        self.stdout.write('')
        
        # Call the thumbnail generation command
        from django.core.management import call_command
        call_command('generate_template_thumbnails')
        
        self.stdout.write('')
        if not options['skip_pdfs']:
            self.stdout.write(self.style.SUCCESS(f'✓ Generated {pdf_success} PDF previews'))
            if pdf_errors > 0:
                self.stdout.write(self.style.WARNING(f'⚠ {pdf_errors} PDF generation errors'))
        self.stdout.write(self.style.SUCCESS('✓ Template previews and thumbnails ready!'))

