CREATE DATABASE netflix_analysis;

USE netflix_analysis;
CREATE TABLE netflix_titles (
    show_id VARCHAR(20),
    type VARCHAR(20),
    title VARCHAR(255),
    director TEXT,
    cast_members TEXT,
    country TEXT,
    date_added DATE,
    release_year INT,
    rating VARCHAR(20),
    duration VARCHAR(30),
    listed_in TEXT,
    description TEXT,
    added_year INT,
    added_month VARCHAR(20),
    added_day INT,
    duration_number INT,
    duration_unit VARCHAR(20)
);

SELECT COUNT(*) AS Total_Titles
FROM netflix_titles;

SELECT
    type,
    COUNT(*) AS Total
FROM netflix_titles
GROUP BY type;

SELECT
    country,
    COUNT(*) AS Titles
FROM netflix_titles
GROUP BY country
ORDER BY Titles DESC
LIMIT 10;


SELECT
    added_year,
    COUNT(*) AS Titles
FROM netflix_titles
GROUP BY added_year
ORDER BY added_year;

SELECT
    director,
    COUNT(*) AS Total
FROM netflix_titles
WHERE director <> 'Unknown'
GROUP BY director
ORDER BY Total DESC
LIMIT 10;

SELECT
    ROUND(AVG(duration_number),2) AS Avg_Duration
FROM netflix_titles
WHERE type='Movie';

SELECT
    title,
    duration_number
FROM netflix_titles
WHERE type='Movie'
ORDER BY duration_number DESC
LIMIT 10;

SELECT
    title,
    duration_number
FROM netflix_titles
WHERE type='TV Show'
ORDER BY duration_number DESC
LIMIT 10;

SELECT
    title,
    release_year
FROM netflix_titles
ORDER BY release_year
LIMIT 10;

SELECT
    title,
    release_year
FROM netflix_titles
ORDER BY release_year DESC
LIMIT 10;

SELECT
    title,
    release_year
FROM netflix_titles
WHERE release_year >= 2018
AND type='Movie';

SELECT
    title,
    duration_number
FROM netflix_titles
WHERE duration_number > 120
AND type='Movie';

SELECT
    rating,
    COUNT(*) AS Movies
FROM netflix_titles
WHERE type='Movie'
GROUP BY rating
ORDER BY Movies DESC;

SELECT
    rating,
    COUNT(*) AS TV_Shows
FROM netflix_titles
WHERE type='TV Show'
GROUP BY rating
ORDER BY TV_Shows DESC;

	SELECT
ROUND(
(
SELECT COUNT(*) FROM netflix_titles WHERE type='TV Show'
)*100.0/
COUNT(*),2) AS TVShow_Percentage
FROM netflix_titles;


SELECT
    release_year,
    COUNT(*) AS Titles
FROM netflix_titles
GROUP BY release_year
ORDER BY Titles DESC
LIMIT 10;

