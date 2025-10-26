<!DOCTYPE html>
<html>
<head>
    <title>Login Page</title>
</head>
<body style="background-color: black; color: yellow; font-family: Arial; text-align: center; margin-top: 100px;">
    <h1 style="color: yellow;">User Login</h1>

    <form method="post" style="display: inline-block; background-color: #222; padding: 30px; border-radius: 15px; box-shadow: 0 0 15px yellow;">
        <div style="margin: 10px;">
            <label style="display: block; margin-bottom: 5px;">Name</label>
            <input type="text" name="name" required style="padding: 8px; width: 250px; border-radius: 5px; border: 1px solid yellow; background: black; color: yellow;">
        </div>
        <div style="margin: 10px;">
            <label style="display: block; margin-bottom: 5px;">Password</label>
            <input type="password" name="pass" required style="padding: 8px; width: 250px; border-radius: 5px; border: 1px solid yellow; background: black; color: yellow;">
        </div>
        <input type="submit" name="login" value="Login" 
               style="background-color: yellow; color: black; padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
    </form>

    <p style="margin-top: 20px;">New user? 
        <a href="register.php" style="color: yellow; text-decoration: underline;">Register here</a>
    </p>

<?php
$con = mysqli_connect("localhost", "root", "root", "users");

if (isset($_POST['login'])) {
    $name = $_POST['name'];
    $password = $_POST['pass'];

    $query = "SELECT * FROM mydata WHERE name='$name' AND password='$password'";
    $result = mysqli_query($con, $query);

    if (mysqli_num_rows($result) > 0) {
        header("Location: welcome.php?user=$name");
        exit();
    } else {
        echo "<p style='color: red; margin-top:20px;'>Access Denied ❌ Wrong name or password</p>";
    }
}
?>
</body>
</html>
