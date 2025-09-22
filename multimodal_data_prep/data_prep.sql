CREATE OR REPLACE TABLE `sm-gemini-playground.retail_shelf.pricing_promotions` (
  product_name STRING,
  category STRING,
  listed_price FLOAT64,
  promo_text STRING,
  promo_price FLOAT64,
  discrepancy_flag STRING
);

INSERT INTO `sm-gemini-playground.retail_shelf.pricing_promotions`
(product_name, category, listed_price, promo_text, promo_price, discrepancy_flag)
VALUES
('Svensk Gurka', 'Vegetables', 16.95, '2 for 30 SEK', 15.00, 'NONE'),
('Proteinbar', 'Snacks', 27.95, '2 for 35 SEK', 17.50, 'PROMO_OK'),
('Mini Jam Jar', 'Condiments', 25.50, '20 SEK each', 20.00, 'DISCOUNT_OK'),
('Havregryn 750g', 'Grains', 21.50, '15 SEK each', 15.00, 'PROMO_OK'),
('Gurka (Chiller)', 'Vegetables', 29.95, '2 for 30 SEK', 15.00, 'PRICE_DISCREP'),
('Pingvin Stång', 'Candy', 5.00, '3 for 12 SEK', 4.00, 'PROMO_OK'),
('Jasminris 1kg', 'Grains', 39.95, '29.90 SEK', 29.90, 'PROMO_OK'),
('Druvor gröna', 'Fruits', 59.95, '25 SEK', 25.00, 'PRICE_DISCREP');


-- more examples from your latest photos
INSERT INTO `sm-gemini-playground.retail_shelf.pricing_promotions`
(product_name, category, listed_price, promo_text, promo_price, discrepancy_flag)
VALUES


-- Honey bay: shelf has two variants/prices in view
('Honung Fast 700g',    'Honey',     69.90, NULL,           NULL,  'NONE'),
('Flytande Honung',     'Honey',     39.95, '35 SEK each',  35.00, 'PROMO_OK'),

-- Chips (Estrella Stjärnor) – ESL shows 15.00 each
('Estrella Stjärnor',   'Snacks',    15.00, NULL,           NULL,  'NONE'),

-- Rye snacks front cart: "2 för 45:-  (Ord. pris 27:95/st.)"
('Finn Crisp Rye Snacks 150g','Snacks',27.95,'2 for 45 SEK',22.50,'PROMO_OK'),

-- Pingvin sticks header sign: "3 för 12:-  (Ord. pris 6:50/st.)"
('Pingvin Stång',       'Candy',      6.50, '3 for 12 SEK',  4.00, 'PROMO_OK'),


('Ekologiska Dadlar',   'Dried Fruit',29.95,'25 SEK each',  25.00, 'PROMO_OK'),

-- Lindt Excellence 100g: "35:-/st  (Ord. pris 51:95/st.)"
('Lindt Excellence 100g','Chocolate', 55.95,'45 SEK each',  45.00, 'PROMO_NOT_OK'),

-- Santa Maria spices dump bin: "20:-/st  (Ord. pris 24:95/st.)"
('Santa Maria Kryddor','Spices',     24.95,'20 SEK each',  20.00, 'PROMO_OK'),



-- Another cucumber set (to pair with your earlier "Gurka (Chiller)" discrepancy demo)
('Gurka Svensk',        'Vegetables', 16.95,'2 for 30 SEK', 15.00, 'PROMO_OK');
