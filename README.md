# BAK Economics – AI-Powered Sales Opportunity Identification

**Authors**: Ana, Damla, Cedric, Tim  
**Mentors**: Stefanie & Ekaterina  
**Program**: Constructor Academy – Data Science & AI Bootcamp  
**Partner**: BAK Economics

---

## Project Overview
This repository contains our capstone project to build an **AI-driven system** for **BAK Economics**. The goal is to automate the identification and qualification of sales opportunities from various documents. This project addresses key challenges faced by the **Analytics and Sales teams**, such as manually sifting through long lists of potential leads. By leveraging capabilities like **PDF OCR, Keyword Extraction, and Predictive Modeling**, we aim to boost **Operational Efficiency** and drive **Revenue** by increasing the number of high-quality **Sales Qualified Opportunities**.

---

## Goal
To implement an intelligent system that automatically scans documents (e.g., PDFs), identifies relevant sales opportunities based on **company fit and offering**, and predicts their potential for success to streamline the sales pipeline.

---

## Milestones
1.  **Data Ingestion & Processing**
    * Develop a pipeline for processing PDFs using OCR.
    * Extract full-text content from the body, not just titles or tags.
    * Incorporate a wider range of data sources.
2.  **Opportunity Identification Engine**
    * Implement keyword extraction using a defined dictionary.
    * Build the core logic for identifying qualified opportunities.
3.  **Predictive Modeling & Learning**
    * Create a model to predict the probability of winning an opportunity.
    * Implement a reinforcement learning loop to refine the model based on sales outcomes (won/lost).
4.  **System Evaluation**
    * Measure the system's impact on the primary KPI: the number of **Sales Qualified Opportunities**.

---

## Data & Inputs
* **Source Documents:** PDFs and other files containing potential leads.
* **Sales Qualification Criteria:** Expert knowledge defining company fit and offering relevance.
* **Keyword Dictionary:** A curated list of terms relevant to BAK Economics' business.
* **Historical Sales Data:** Past opportunity outcomes (won/lost) for model training.

---

## Tech Stack
* **Python:** For building the data processing pipeline and machine learning models (OCR, keyword extraction, prediction).
* **Machine Learning Libraries:** For implementing the opportunity identification and prediction logic.
* **Git / GitLab:** For version control and collaborative development.