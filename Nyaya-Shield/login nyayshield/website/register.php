<!DOCTYPE html>
<html>
<head>
    <title>Register</title>
</head>
<body style="background-color: black; color: yellow; font-family: Arial; text-align: center; margin-top: 100px;">
    <h1 style="color: yellow;">Create New Account</h1>

    <form method="post" style="display: inline-block; background-color: #222; padding: 30px; border-radius: 15px; box-shadow: 0 0 15px yellow;">
        <div style="margin: 10px;">
            <label style="display: block; margin-bottom: 5px;">Name</label>
            <input type="text" name="name" required style="padding: 8px; width: 250px; border-radius: 5px; border: 1px solid yellow; background: black; color: yellow;">
        </div>
        <div style="margin: 10px;">
            <label style="display: block; margin-bottom: 5px;">Email</label>
            <input type="email" name="email" required style="padding: 8px; width: 250px; border-radius: 5px; border: 1px solid yellow; background: black; color: yellow;">
        </div>
        <div style="margin: 10px;">
            <label style="display: block; margin-bottom: 5px;">Password</label>
            <input type="password" name="pass" required style="padding: 8px; width: 250px; border-radius: 5px; border: 1px solid yellow; background: black; color: yellow;">
        </div>
        <input type="submit" name="register" value="Register" 
               style="background-color: yellow; color: black; padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
    </form>

    <p style="margin-top: 20px;">Already have an account? 
        <a href="index.php" style="color: yellow; text-decoration: underline;">Login here</a>
    </p>

<?php
$con = mysqli_connect("localhost", "root", "root", "users");

if (isset($_POST['register'])) {
    $name = $_POST['name'];
    $email = $_POST['email'];
    $password = $_POST['pass'];

    // Check if user already exists
    $check = "SELECT * FROM mydata WHERE name='$name' OR email='$email'";
    $result = mysqli_query($con, $check);

    if (mysqli_num_rows($result) > 0) {
        echo "<p style='color:red; margin-top:20px;'>User already exists ❌</p>";
    } else {
        $query = "INSERT INTO mydata (name, email, password) VALUES ('$name', '$email', '$password')";
        if (mysqli_query($con, $query)) {
            echo "<p style='color:lightgreen; margin-top:20px;'>Registration successful ✅</p>";
        } else {
            echo "<p style='color:red; margin-top:20px;'>Error while registering ❌</p>";
        }
    }
}
?>
</body>
</html>
