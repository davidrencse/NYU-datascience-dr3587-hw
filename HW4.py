
# Actors and Directors Who Cooperated at Least Three Times
#SQL
SELECT actor_id, director_id
FROM ActorDirector
GROUP BY actor_id, director_id
HAVING COUNT(*) >= 3;

#PANDAS
# ActorDirector: actor_id, director_id, timestamp
out = (ActorDirector
       .groupby(['actor_id','director_id'])
       .size()
       .reset_index(name='cnt')
       .query('cnt >= 3')[['actor_id','director_id']])

# Fix Names in a Table

#SQL
SELECT user_id,CONCAT(UPPER(LEFT(name, 1)), LOWER(SUBSTRING(name, 2))) AS name
FROM Users
ORDER BY user_id;

#PANDAS
# Users: user_id, name
Users = Users.sort_values('user_id').copy()
Users['name'] = Users['name'].str.capitalize()
out = Users[['user_id','name']]

#Combine Two Tables

#SQL
SELECT p.FirstName, p.LastName, a.City, a.State
FROM Person p
LEFT JOIN Address a
  ON p.PersonId = a.PersonId;

#PANDAS
# Person: personId, firstName, lastName
# Address: personId, city, state
out = (Person
       .merge(Address, on='personId', how='left')
       [['firstName','lastName','city','state']])

# Second Highest Salary

#SQL 
SELECT MAX(salary) AS SecondHighestSalary
FROM Employee
WHERE salary < (SELECT MAX(salary) FROM Employee);

#PANDAS
WITH r AS (
  SELECT salary,
         DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM Employee
)
SELECT CASE WHEN COUNT(*) = 0 THEN NULL ELSE MAX(salary) END AS SecondHighestSalary
FROM r
WHERE rk = 2;

# List the Products Ordered in a Period

# SQL
SELECT p.product_name, SUM(o.quantity) AS total_units
FROM Products p
JOIN Orders o
  ON p.product_id = o.product_id;
GROUP BY p.product_id, p.product_name;
HAVING SUM(o.quantity) >= 100;

# PANAS
orders = Orders.copy()
orders['order_date'] = pd.to_datetime(orders['order_date'])
mask = (orders['order_date'] >= '2020-02-01') & (orders['order_date'] <= '2020-02-29')
tot = (orders.loc[mask]
       .groupby('product_id', as_index=False)['quantity'].sum()
       .rename(columns={'quantity':'total_units'}))
out = (tot
       .merge(Products[['product_id','product_name']], on='product_id')
       .query('total_units >= 100')[['product_name','total_units']])


# Replace Employee ID With the Unique Identifier


#SQL
SELECT eu.unique_id, e.name
FROM Employees e
LEFT JOIN EmployeeUNI eu
  ON e.id = eu.id;

#PANDAS
# Employees: id, name
# EmployeeUNI: id, unique_id
out = (Employees
       .merge(EmployeeUNI, on='id', how='left')
       [['unique_id','name']])

# Game Play Analysis IV

# SQL
WITH first_login AS (
  SELECT player_id, MIN(event_date) AS first_login
  FROM Activity
  GROUP BY player_id
)
SELECT ROUND(AVG(a2.player_id IS NOT NULL), 2) AS fraction
FROM first_login f
LEFT JOIN Activity a2
  ON a2.player_id = f.player_id
 AND a2.event_date = DATE_ADD(f.first_login, INTERVAL 1 DAY);

# PANDAS
# Activity: player_id, device_id, event_date, games_played
act = Activity.copy()
act['event_date'] = pd.to_datetime(act['event_date'])
first = act.groupby('player_id', as_index=False)['event_date'].min().rename(columns={'event_date':'first_login'})
chk = first.merge(act[['player_id','event_date']],
                  on='player_id', how='left')
chk['next_day'] = chk['first_login'] + pd.Timedelta(days=1)
hit = (chk['event_date'] == chk['next_day']).groupby(chk['player_id']).any()
fraction = round(hit.mean(), 2)
out = pd.DataFrame({'fraction':[fraction]})


#Project Employees I

#SQL
SELECT p.project_id,
       ROUND(AVG(e.experience_years), 2) AS average_years
FROM Project p
JOIN Employee e
  ON p.employee_id = e.employee_id
GROUP BY p.project_id;

#PANDAS
# Project: project_id, employee_id
# Employee: employee_id, experience_years
out = (Project
       .merge(Employee, on='employee_id', how='inner')
       .groupby('project_id', as_index=False)['experience_years']
       .mean())
out['average_years'] = out['experience_years'].round(2)
out = out[['project_id','average_years']]

#Department Top Three Salaries

#SQL
WITH ranked AS (
  SELECT d.name AS Department,
         e.name AS Employee,
         e.salary,
         DENSE_RANK() OVER (PARTITION BY d.id ORDER BY e.salary DESC) AS rk
  FROM Employee e
  JOIN Department d
    ON e.departmentId = d.id
)
SELECT Department, Employee, salary
FROM ranked
WHERE rk <= 3;

#PANAS
# Employee: id, name, salary, departmentId
# Department: id, name
df = (Employee
      .merge(Department, left_on='departmentId', right_on='id', how='inner',
             suffixes=('_emp','_dept')))
df['rk'] = (df
            .sort_values(['id_dept','salary'], ascending=[True, False])
            .groupby('id_dept')['salary']
            .rank(method='dense', ascending=False))
out = (df.query('rk <= 3')
         .rename(columns={'name_dept':'Department','name_emp':'Employee'})
         [['Department','Employee','salary']])
