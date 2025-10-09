# Analysis Improvement Plan

**Project Goal:** To significantly improve the analysis outcome by making it more user-friendly for visually impaired students, providing actionable insights for learning, and delivering structured data to an external exercise-generation module.

---

## TODO List

- [x] **Phase 0: Foundational Database Upgrade**
  - [x] Modify `phoneme_results` table schema in `db.py`.
  - [x] Modify `grammar_results` table schema in `db.py`.
  - [x] Modify `user_analytics_cache` table schema in `db.py`.
  - [x] Update `save_phoneme_result` function in `db.py`.
  - [x] Update `save_grammar_result` function in `db.py`.
  - [x] Update `upsert_user_analytics_cache` function in `db.py`.

- [x] **Phase 1: Enhance Real-time Pronunciation Analysis (`/analyze/both`)**
  - [x] Implement word-level analysis and WER calculation in `utils_phone.py`.
  - [x] Implement pronunciation weakness categorization in `utils_phone.py`.
  - [x] Update `/analyze/both` endpoint in `main.py` to return the new analysis structure.
  - [x] Create/update response schemas in `schemas.py` for the new analysis structure.

- [x] **Phase 2: Implement AI-Powered Grammar Categorization**
  - [x] Create `categorize_grammar_error` function in `utils_openai.py`.
  - [x] Integrate categorization into `gec_correct` and `gec_speech` endpoints in `main.py`.

- [x] **Phase 3: Create New Paginated Weaknesses Endpoint (`/weaknesses/{user_id}`)**
  - [x] Create `fetch_user_weaknesses` database query function in `db.py`.
  - [x] Define `WeaknessOut` and `PaginatedWeaknessesOut` schemas in `schemas.py`.
  - [x] Implement the `/weaknesses/{user_id}` endpoint in `main.py`.

- [x] **Phase 4: Supercharge the 7-Day Analytics (`/analytics/{user_id}`)**
  - [x] Update `compute_last7d` in `analytics.py` to calculate top pronunciation and grammar weaknesses.
  - [x] Update `format_analytics_response` in `main.py` to include the new analytics data.
  - [x] Update `AnalyticsOut` and related schemas in `schemas.py`.

---

## Detailed Plan

### Phase 0: Foundational Database Upgrade

The first step is to upgrade the database schema. This is a critical prerequisite for all subsequent features as it prepares the database to store the new, richer analysis data.

- **`phoneme_results` table:** Will be modified to store word-level pronunciation analysis, including the Word Error Rate (WER), a detailed breakdown for each word, and categorized pronunciation weaknesses based on `topics.md`.
- **`grammar_results` table:** Will be updated to store the categorized grammar weaknesses (from `topics.md`) identified by the LLM.
- **`user_analytics_cache` table:** Will be enhanced to store aggregated top pronunciation and grammar weaknesses over a 7-day period.

### Phase 1: Enhance Real-time Pronunciation Analysis (`/analyze/both`)

This phase focuses on transforming the technical phoneme output into immediate, understandable, and actionable feedback.

1.  **Word-by-Word Analysis:** The core of this phase is to shift from phonemes to words. The API response will provide a list of words from the user's speech, marking each as "correct" or "incorrect."
2.  **Detailed & Categorized Errors:** For each incorrect word, the API will explain the error in simple terms (e.g., "the 'th' sound was missed") and provide the weakness category from `topics.md` (e.g., `"pronunciation_th_vs_t"`).
3.  **Word Error Rate (WER):** A top-level WER score will be included to give a simple, overall measure of pronunciation accuracy for the entire sentence.

### Phase 2: Implement AI-Powered Grammar Categorization

This phase leverages a Large Language Model (LLM) to automatically categorize grammar mistakes, providing consistent and accurate labeling.

1.  **LLM Integration:** A new function will be created to communicate with an AI model. This function will send the user's original text and the corrected version.
2.  **Categorization:** The AI will be instructed to act as an expert grammar teacher, analyze the correction, and classify the mistake according to the grammar topics defined in `topics.md` (e.g., `"subject_verb_agreement"`).
3.  **Data Storage:** These categories will be saved alongside every grammar correction, building a rich history of the user's specific challenges.

### Phase 3: Create New Paginated Weaknesses Endpoint (`/weaknesses/{user_id}`)

As you suggested, a dedicated endpoint to retrieve a history of a user's weaknesses is an excellent addition.

1.  **New Endpoint:** I will create a new endpoint, `/weaknesses/{user_id}`.
2.  **Functionality:** This endpoint will retrieve all historical pronunciation and grammar weaknesses for a specific user, complete with the original text for context.
3.  **Pagination:** The endpoint will be paginated (using `limit` and `offset` parameters) to ensure it is efficient and can handle a long history of user data.

### Phase 4: Supercharge the 7-Day Analytics (`/analytics/{user_id}`)

The final phase is to make the weekly analytics summary smarter and more insightful.

1.  **Top Weaknesses:** The analytics engine will be upgraded to process the newly available data, identifying and highlighting the user's top 3-5 most frequent pronunciation and grammar weaknesses from the past week.
2.  **Refined Metrics:** I will refine existing metrics, such as the "top phoneme substitutions," to ensure they are accurate and meaningful in the Sri Lankan English (SLE) context.
3.  **Actionable Headlines:** The AI-generated "headline message" will be improved to provide specific, encouraging, and actionable advice based directly on the user's identified top weaknesses.