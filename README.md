Custom Cloud Storage is essentially [Local File Sharing](https://github.com/MahinBro001238/LocalFileSharing/) taken further. It keeps the same idea of hosting your own file storage and accessing it through a browser, but layers proper cloud storage behaviour on top of it. Instead of a single shared password, every user has their own account with their own isolated storage space, and the whole thing behaves much closer to something like Google Drive running on your own machine rather than a simple file server

Accounts are created through a signup page using an email and password. New accounts are not immediately active. An admin has to verify each account and manually allocate how much storage space that user gets before they can start using the system. This keeps the server from being open to anyone who finds it and gives the admin full control over who has access and how much space they are allowed to use. Once verified, users can log in and access their own personal storage space, completely separate from every other user on the server

From there the experience is the same as Local File Sharing. Users can browse folders, upload files and folders, download anything, rename, copy, move, and delete files, and perform bulk operations across multiple items at once. Each user only ever sees their own files, and the storage they use is tracked against their allocated limit

Accounts come with the usual cloud storage account management you would expect. Users can change their password, change their email address, and delete their account entirely. Password changes and email changes both go through an email verification step, so a code is sent to the relevant address before anything is confirmed. Passwords are stored as SHA256 hashes rather than plain text. Sessions are tied to a generated session ID stored alongside the account, so changing a password immediately invalidates any other active sessions for that account

Under the hood each user's files live in their own folder named after their email address inside the data directory. Account information is stored in a per-user JSON file. The app uses Gmail's SMTP server to send verification emails, so a Gmail account and an app password are required to run it. On first run the app walks through a short setup process to collect these details and create the data directory

This app has no config file. Any custom behaviour such as changing the port or storage paths requires modifying the source code directly

The UI was designed for use on a desktop or laptop browser and was not built with mobile ease of use in mind. It will still function on a mobile browser but the experience is not optimised for it

This app was built and tested on Windows 10/11 and Android using Termux however it should work with macOS and Linux as well

This app depends on Flask and natsort

- On first run the app will walk you through setup, including entering your Gmail address and app password for sending verification emails. Visit https://support.google.com/mail/answer/185833 to learn how to generate a Gmail app password
- Run with `python Custom_Cloud_Storage.py` after setup
- Access it from any device on the same network at `http://<your-device-ip>:5003`
- To find your device IP: `ipconfig` on Windows, `ifconfig` or `ip a` on macOS/Linux, on Android go to Settings → Wi-Fi → tap your connected network → the IP address will be listed under the network details
- Admin account verification is done directly through the data folder. Each user's account info is stored in a JSON file under their email folder where you can set `admin_verified` to `true` and assign `allocated_space_in_bytes`

Licensed under the Apache License 2.0
