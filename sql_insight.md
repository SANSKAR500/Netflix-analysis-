## SQL Insights

The dataset was analyzed using SQL to answer various business and content-related questions about Netflix's catalog.

### Database Setup
- Created a dedicated database named `netflix_analysis`.
- Designed a `netflix_titles` table with cleaned and transformed columns such as:
  - `added_year`
  - `added_month`
  - `added_day`
  - `duration_number`
  - `duration_unit`

---

## Exploratory SQL Analysis

### 1. Total Content Available
- Counted the total number of titles available in the Netflix dataset.
- Used `COUNT(*)` to determine the size of the catalog.

---

### 2. Movies vs TV Shows
- Compared the number of Movies and TV Shows.
- Grouped records by content type to understand catalog distribution.

---

### 3. Top 10 Countries by Content
- Identified the countries contributing the highest number of Netflix titles.
- Sorted results in descending order to find the leading content-producing countries.

---

### 4. Content Added Over the Years
- Analyzed how many titles were added to Netflix each year.
- Helped identify periods of rapid catalog expansion.

---

### 5. Most Prolific Directors
- Ranked directors based on the number of titles they directed.
- Excluded unknown directors for more meaningful analysis.

---

### 6. Average Movie Duration
- Calculated the average runtime of movies.
- Used the cleaned numeric duration column for accurate computation.

---

### 7. Longest Movies
- Retrieved the top 10 longest movies available on Netflix.
- Sorted movies by duration in descending order.

---

### 8. Longest TV Shows
- Identified TV Shows with the highest number of seasons.
- Ranked shows based on season count.

---

### 9. Oldest Titles
- Listed the earliest released titles in the Netflix catalog.
- Helped understand the historical range of available content.

---

### 10. Latest Titles
- Retrieved the most recently released titles.
- Showed the newest content available in the dataset.

---

### 11. Movies Released Since 2018
- Filtered movies released in or after 2018.
- Useful for analyzing recent content trends.

---

### 12. Movies Longer Than 120 Minutes
- Identified movies exceeding two hours in runtime.
- Demonstrated SQL filtering using conditional statements.

---

### 13. Movie Rating Distribution
- Counted movies by content rating (PG, TV-MA, etc.).
- Helped understand audience targeting.

---

### 14. TV Show Rating Distribution
- Analyzed ratings specifically for TV Shows.
- Compared certification trends across television content.

---

### 15. Percentage of TV Shows
- Calculated what percentage of the Netflix catalog consists of TV Shows.
- Used SQL subqueries and percentage calculations.

---

### 16. Release Year Popularity
- Determined which release years contributed the highest number of titles.
- Ranked years by content count.

---

## SQL Concepts Demonstrated

- Database creation
- Table creation
- Data aggregation (`COUNT`, `AVG`)
- Filtering (`WHERE`)
- Grouping (`GROUP BY`)
- Sorting (`ORDER BY`)
- Limiting results (`LIMIT`)
- Aggregate functions
- Subqueries
- Percentage calculations
- Data cleaning with transformed columns