CREATE TABLE member (
	member_id VARCHAR(50) UNIQUE NOT NULL PRIMARY KEY,
	password VARCHAR(50) NOT NULL,
	first_name CHAR(20) NOT NULL,
	last_name CHAR(20) NOT NULL,
	phone_number VARCHAR(15),
	register_date DATE,
	birthday DATE,
	card_number VARCHAR(12)
);

CREATE TABLE metrics(
	member_id VARCHAR(50) REFERENCES member(member_id),
	weight INT,
	rest_heart_rate INT,
	pace INT,
	blood_pressure VARCHAR(7),
	sleep_start TIME,
	sleep_end TIME
);

CREATE TABLE exercise(
	exercise_id SERIAL UNIQUE NOT NULL PRIMARY KEY,
	routine_name VARCHAR(50),
	sets INT,
	reps INT,
	weight INT,
	distance INT,
	date DATE,
	start_time TIME,
	end_time TIME
);

CREATE TABLE goals(
	member_id VARCHAR(50) NOT NULL REFERENCES member(member_id),
	exercise_id INT REFERENCES exercise(exercise_id),
	description TEXT
);

CREATE TABLE completed(
	member_id VARCHAR(50) NOT NULL REFERENCES member(member_id),
	exercise_id INT NOT NULL REFERENCES exercise(exercise_id)
);

CREATE TABLE trainer(
	trainer_id VARCHAR(50) UNIQUE NOT NULL PRIMARY KEY,
	password VARCHAR(50) NOT NULL, 
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	phone_number VARCHAR(15),
    description TEXT
);

CREATE TABLE trainer_availability(
	schedule_id SERIAL PRIMARY KEY,
	trainer_id VARCHAR(50) NOT NULL REFERENCES trainer(trainer_id),
	date DATE,
	start_time TIME,
	end_time TIME
);

CREATE TABLE admin(
	admin_id VARCHAR(50) NOT NULL UNIQUE PRIMARY KEY,
	password VARCHAR(50) NOT NULL,
	first_name VARCHAR(50),
	last_name VARCHAR(50)
);

CREATE TABLE room(
	room_id VARCHAR(50) NOT NULL UNIQUE PRIMARY KEY ,
	description TEXT
);

CREATE TABLE class(
	class_id SERIAL PRIMARY KEY,
	name VARCHAR(50) NOT NULL,
	trainer_id VARCHAR(50) REFERENCES trainer(trainer_id) NOT NULL,
	description TEXT,
	cost INT,
	capacity INT
);

CREATE TABLE session(
	session_id SERIAL PRIMARY KEY,
	trainer_id VARCHAR(50) NOT NULL REFERENCES trainer(trainer_id),
	member_id VARCHAR(50) NOT NULL REFERENCES member(member_id),
	session_type VARCHAR(50),
	date DATE NOT NULL,
	start_time TIME NOT NULL,
	end_time TIME NOT NULL,
	location VARCHAR(50) REFERENCES room(room_id) 
);

CREATE TABLE bookings(
	class_id INT NOT NULL REFERENCES class(class_id),
	room_id VARCHAR(50) NOT NULL REFERENCES room(room_id),
	date DATE NOT NULL,
	start_time TIME NOT NULL,
	end_time TIME NOT NULL
);

CREATE TABLE member_schedule(
	member_id VARCHAR(50) NOT NULL REFERENCES member(member_id),
	class_id INT NOT NULL NOT NULL REFERENCES class(class_id)
);

CREATE TABLE equipment(
	equipment_id SERIAL PRIMARY KEY,
	equipment_name VARCHAR(50) NOT NULL,
	maintinence_date DATE,
	location VARCHAR(50) REFERENCES room(room_id)
);

CREATE TABLE billing(
	billing_id SERIAL PRIMARY KEY,
	admin_id VARCHAR(50) REFERENCES admin(admin_id) NOT NULL,
	member_id VARCHAR(50) REFERENCES member(member_id) NOT NULL,
	type VARCHAR(50),
	date DATE,
	amount INT
);