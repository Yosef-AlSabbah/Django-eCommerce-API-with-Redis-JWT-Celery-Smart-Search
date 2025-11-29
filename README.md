# Hypex E-commerce API

Welcome to the Hypex E-commerce API, a scalable and feature-rich backend solution built with Django and Django REST Framework.

## Core Features

-   **Clean & Modular Architecture**: Organized into logical Django apps for maintainability.
-   **Complete E-commerce Functionality**: Covers products, carts, orders, payments, coupons, and more.
-   **JWT Authentication**: Secure, token-based authentication powered by `djoser` and `simple_jwt`.
-   **Interactive API Documentation**: Auto-generated, interactive API docs using `drf-spectacular` (OpenAPI 3).
-   **Asynchronous Task Processing**: Uses `Celery` with a `Redis` broker for handling background tasks like sending emails.
-   **Performance Optimized**: Implements caching with `Redis` and rate limiting (throttling) to ensure a fast and reliable API.
-   **Containerized with Docker**: Comes with a complete Docker and Docker Compose setup for easy development and deployment.

## Getting Started

This project is fully containerized. All you need is Docker and Docker Compose to get it up and running.

### Prerequisites

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/m-h-s/E-commerce-api.git
    cd E-commerce-api
    ```

2.  **Create Environment File**
    The project uses an `.env` file for configuration. A `.env.example` is provided as a template. Simply copy it to create your own configuration file:
    ```bash
    cp .env.example .env
    ```
    You can customize the variables inside `.env` if needed, but the default values are configured to work with the Docker setup.

3.  **Build and Run with Docker Compose**
    This single command will build the Docker images, create the containers, and run all the services:
    ```bash
    docker-compose up -d --build
    ```

    This will start the following services:
    -   `web`: The Django application running on Gunicorn.
    -   `database`: A PostgreSQL database for data storage.
    -   `cache`: A Redis instance for caching and Celery.
    -   `celery_worker`: A Celery worker for processing asynchronous tasks.
    -   `celery_beat`: A Celery beat scheduler for periodic tasks.
    -   `flower`: A web-based monitoring tool for Celery.
    -   `nginx`: A reverse proxy for the Django application and serving static files.

## Usage

Once the containers are running, you can access the following services:

-   **API**: The API is available at `http://localhost:80/api/v1/`.
-   **Interactive API Documentation (Swagger UI)**: `http://localhost:80/api/v1/docs/`
-   **Celery Monitoring (Flower)**: `http://localhost:5555/`

## Running Tests

To run the test suite, execute the following command in your terminal. This will run the tests inside the `web` container.

```bash
docker-compose exec web pytest
```
