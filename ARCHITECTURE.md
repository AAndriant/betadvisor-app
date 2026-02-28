# Architecture & Workflow

## Overview
This document outlines the current workflow for the Betting Ticket OCR Extraction module within the BetAdvisor application.

## 1. Data Ingestion
*   **Source:** User uploads an image of a betting ticket.
*   **Model:** `Ticket` (src/tickets/models.py)
*   **Storage:** Image is stored locally (or S3 in prod) via `ImageField`.
*   **Initial Status:** `PENDING_OCR`

## 2. Processing Trigger
*   **Trigger:** Currently appears to be a synchronous or task-based call to `process_ticket_image(ticket_id)` in `src/tickets/logic.py`.
*   **Service:** `GeminiOCRService` (src/tickets/services.py).

## 3. OCR Extraction (AI Layer)
*   **Provider:** Google Gemini (via `google.generativeai`).
*   **Model:** `gemini-2.0-flash`.
*   **Input:** Raw image (PIL Image).
*   **Prompt:** Hardcoded prompt asking for specific JSON structure (bookmaker, stake, payout, bets).
*   **Output:** JSON text (parsed from Markdown code blocks).

## 4. Data Parsing & Validation
*   **Raw Data:** Stored in `Ticket.ocr_raw_data`.
*   **Parsing Logic:**
    *   Iterates through `bets` array from JSON.
    *   **Match Linking (Weak Link):** Attempts to link the extracted `match_name` to an existing `Match` in the database.
        *   *Heuristic:* Splits the match string and performs `icontains` search on `home_team` or `away_team`.
        *   *Fallback:* If no match found, defaults to `Match.objects.last()` (Risk of incorrect data).
    *   **Atomicity:** Uses `transaction.atomic()` to ensure all bets are created or none.

## 5. Persistence (Database)
*   **Models:**
    *   `Ticket`: Status updated to `VALIDATED` (or `REJECTED` on error).
    *   `BetSelection`: Rows created for each extracted bet, linked to `Ticket` and `Match`.
*   **Data Types:** Financial values (Odds, Stake) are stored using `DecimalField` (Good practice).

## Current Workflow Diagram

```
[User Upload] -> [Ticket Created (PENDING_OCR)]
                        |
                        v
                [process_ticket_image]
                        |
                        v
              [GeminiOCRService Call]
            (Image -> Gemini 2.0 Flash)
                        |
                        v
                  [JSON Response]
                        |
                        v
            [Match Lookup / Linking Logic]
                        |
            +-----------+-----------+
            |                       |
    [Match Found/Default]     [Error/Exception]
            |                       |
            v                       v
    [Create BetSelections]   [Status = REJECTED]
    [Status = VALIDATED]
```
