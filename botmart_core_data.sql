--
-- PostgreSQL database dump
--

\restrict 6b6nssKCKPAzCrb2CJ5sXd2QGsObAy74P7ik6cY92SRB0gDjEKdUGkPZC7TkfhK

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clients (id, business_name, email, hashed_password, phone_number_id, whatsapp_number, access_token, is_active, created_at, token_valid, plan, payment_status, payment_reference, waba_id, subscription_start, subscription_end, grace_period_end, reminder_7_sent, reminder_3_sent, ai_replies_used, ai_replies_reset_date, subscription_months, business_description) FROM stdin;
6	Klassic Hairs	msnonuorah3964@gmail.com	$2b$12$2jY2Vq8tJ9TTw159Fz0fruvb8syKO3AKJUCXgk5oGsz7XhNFdCFOG	1028026527054528	+2348103491026	EAAUJzVYGvkgBQ3ZBddfDHwlYU7ansczwVoUgp6BeMmE2ga1vKpFdHMfa1uS5VhWHOBwN3WTgonV4ZClrZB5M8MjhYlo4Q22BShz44g1fG0hEOah1ErZBeEbR16PzAU8ZCvzTwWIF3mpwZBQZBjFlIxdMwt9DMjBKYSjIsAaVKmS9WT6yLmxAXsQhDTTKSFX31cxf7qNZACoUHxQ1GvXJ1MdwoXkg9pmG95i9vB8k	t	2026-03-07 01:40:17.146631	t	pro	paid	rkggo79utq	918538821086247	2026-03-11	2029-05-05	2029-05-12	f	f	1	2026-03-12	1	\N
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (id, client_id, name, description, price, image_url, category, keyword, is_active, created_at, image_public_id) FROM stdin;
\.


--
-- Data for Name: subscription_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.subscription_plans (id, name, display_name, price_kobo, description, is_active, created_at, updated_at, price_naira, discount_12_months, discount_3_months, discount_6_months) FROM stdin;
3	pro	Pro	3500000	Everything in Growth + unlimited AI + dedicated support	t	\N	2026-03-03 14:50:35.344918	35000	20	10	15
2	growth	Growth	2000000	Unlimited contacts, rules, products + broadcasts + AI replies	t	\N	2026-03-03 14:50:35.352151	20000	20	10	15
1	starter	Starter	900000	1 WhatsApp number, 500 contacts, 10 rules, 10 products	t	\N	2026-03-03 14:50:35.354468	9000	20	10	15
\.


--
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clients_id_seq', 6, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: subscription_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subscription_plans_id_seq', 3, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 6b6nssKCKPAzCrb2CJ5sXd2QGsObAy74P7ik6cY92SRB0gDjEKdUGkPZC7TkfhK

