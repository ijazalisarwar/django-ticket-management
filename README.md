# Ticket Management

Ticket Management is a platform for ticket exchange, providing users with information about events and venues sourced from the Ticket Master Discovery API.

## Overview

The project consists of two main components:

1. **Django Web Application:**
   - Frontend and backend functionalities are implemented using Django.
   - PostgreSQL is used as the database to store and manage data.
   - The Django application is responsible for user interactions, exchanging tickets, displaying events and venues, and managing the overall user experience.

2. **AWS Lambda Functions:**
   - AWS Lambda functions are utilized to fetch data from the Ticket Master Discovery API.
   - The retrieved data is then processed and added to the following tables:
     - Events
     - Venues
     - Classifications

## Merge `development` to `production` branch

We are using forward merging to merge the `development` branch to the `production` branch.

1. Create a pull request to merge the `development` branch to the `production` branch.

2. To merge the `development` branch to the `production` branch, run these commands in your terminal (GitHub does not support forward merging, so you have to do it manually in your terminal):

    ```bash
    git pull
    git checkout production
    git merge origin/development
    git push origin production
    ```

## Getting Started

To set up and run the project locally, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/triplek-tech/django-tickets.git
    cd django-tickets
    ```

2. Install Dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run Migrations:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4. Run Server:

    ```bash
      python manage.py runserver
    ```

5. Access the application in your web browser at `http://localhost:8000`

AWS Lambda Function
To set up and run the aws lambda functions locally, follow these steps:
1-Docker:
you must have docker to run lambda functions
2- cd ticket-master-api
3- sam build
4- sam local start-api
By you can see 2 endpoints
  1-http://127.0.0.1:3000/venues
  2-http://127.0.0.1:3000/events

Environment Variables
Ensure to set the necessary environment variables for the Lambda functions, including API keys and other configurations.

Contributing
Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please feel free to open an issue or create a pull request.
