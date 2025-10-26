<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
</head>
<body style="background-color: black; color: yellow; font-family: Arial; text-align: center; margin-top: 100px;">
    <?php
    if (isset($_GET['user'])) {
        $user = htmlspecialchars($_GET['user']);
        echo "<h1 style='font-size: 40px;'>Welcome, $user! 🥳</h1>";
        echo "<p style='margin-top: 20px;'>You have successfully logged in.</p>";
    } else {
        echo "<h1 style='color: red;'>Access Denied ❌</h1>";
    }
    ?>
    <a href='index.php' style='display:inline-block; margin-top:30px; background:yellow; color:black; padding:10px 20px; border-radius:5px; text-decoration:none;'>Logout</a>
</body>
</html>
