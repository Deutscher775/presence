function updatePresence(presence) {
    console.log('Updating presence:', presence);

    // 1. Banner
    let banner = document.getElementById("bgimage");
    if (presence.banner) {
        if (!banner) {
            banner = document.createElement("img");
            banner.id = "bgimage";
            banner.className = "bgimage";
            const profileCard = document.getElementById("profile-card");
            if (profileCard) profileCard.insertBefore(banner, profileCard.firstChild);
        }
        banner.src = presence.banner;
        banner.style.display = "block";
        banner.style.filter = "blur(5px) brightness(0.5)";
    } else if (banner) {
        banner.style.display = "none";
    }

    // 2. Hidden user
    const avatarDiv = document.querySelector(".avatar");
    if (presence.hidden) {
        if (avatarDiv) avatarDiv.style.display = "none";
        const statusDot = document.getElementById("STATUS_DOT");
        if (statusDot) statusDot.style.display = "none";
    } else {
        if (avatarDiv) avatarDiv.style.display = "block";
        let statusDot = document.getElementById("STATUS_DOT");
        if (!statusDot) {
            statusDot = document.createElement("div");
            statusDot.id = "STATUS_DOT";
            document.body.appendChild(statusDot); // Adjust container
        }
        statusDot.style.display = "block";
        statusDot.className = `status-dot ${presence.status || ""}`;
    }

    // Username
    const usernameTag = document.getElementById("USERNAME");
    if (usernameTag && !presence.hidden) {
        usernameTag.innerHTML = "";
        const a = document.createElement("a");
        a.href = `https://discordapp.com/users/${presence.userid || ""}`;
        a.target = "_blank";
        a.textContent = presence.username || "";
        usernameTag.appendChild(a);
    }

    // Status Dot IMG
    let statusDotImg = document.getElementById("STATUS_DOT_IMG");
    if (!statusDotImg) {
        statusDotImg = document.createElement("img");
        statusDotImg.id = "STATUS_DOT_IMG";
        document.body.appendChild(statusDotImg); // Adjust container
    }
    statusDotImg.src = `https://api.deutscher775.de/presence/status_icons/${presence.status || "online"}.png`;

    // Custom Status
    let customStatusTag = document.getElementById("CUSTOM_STATUS");
    if (!customStatusTag && (presence.custom_status || presence.custom_status_emoji)) {
        customStatusTag = document.createElement("div");
        customStatusTag.id = "CUSTOM_STATUS";
        document.body.appendChild(customStatusTag); // Adjust container
    }

    if (customStatusTag) {
        if (presence.custom_status || presence.custom_status_emoji) {
            customStatusTag.innerHTML = "";
            if (presence.custom_status_emoji) {
                const emojiImg = document.createElement("img");
                emojiImg.id = "CUSTOM_STATUS_EMOJI";
                emojiImg.src = presence.custom_status_emoji;
                emojiImg.alt = "";
                emojiImg.style = "vertical-align: middle; height: 20px; width: 20px; margin: 0; margin-right: 5px; border-radius: 0;";
                customStatusTag.appendChild(emojiImg);
            }
            if (presence.custom_status !== "Custom Status") {
                customStatusTag.appendChild(document.createTextNode(presence.custom_status || ""));
            }
            customStatusTag.style.display = "block";
        } else {
            customStatusTag.style.display = "none";
        }
    }

    // Avatar
    const userAvatar = document.getElementById("USER_AVATAR");
    if (userAvatar) {
        userAvatar.src = presence.avatar || "";
    }

    // Activities
    let activities = presence.activities || [];
    if (activities.length === 0) {
        activities = [{
            name: "I'm not doing anything",
            assets: { large_image_url: null, small_image_url: null },
            timestamps: { start: null, end: null }
        }];
    }
    let activity = activities[0];
    if (activity.name === "Custom Status" && activities.length > 1) {
        activity = activities[1];
    } else if (activity.name === "Custom Status" && activities.length === 1) {
        activity.name = "I'm not doing anything";
    }

    // Large image
    let largeImageTag = document.getElementById("LARGE_IMAGE_URL");
    if (!largeImageTag && activity.assets?.large_image_url) {
        largeImageTag = document.createElement("img");
        largeImageTag.id = "LARGE_IMAGE_URL";
        document.body.appendChild(largeImageTag); // Adjust container
    }
    if (largeImageTag) {
        if (activity.assets?.large_image_url) {
            largeImageTag.src = activity.assets.large_image_url;
            largeImageTag.style.display = "block";
        } else {
            largeImageTag.style.display = "none";
        }
    }

    // Small image
    let smallImageTag = document.getElementById("SMALL_IMAGE_URL");
    if (!smallImageTag && activity.assets?.small_image_url) {
        smallImageTag = document.createElement("img");
        smallImageTag.id = "SMALL_IMAGE_URL";
        document.body.appendChild(smallImageTag); // Adjust container
    }
    if (smallImageTag) {
        if (activity.assets?.small_image_url) {
            smallImageTag.src = activity.assets.small_image_url;
            smallImageTag.style.display = "block";
        } else {
            smallImageTag.style.display = "none";
        }
    }

    // Presence name
    const presenceNameTag = document.getElementById("PRESENCE_NAME");
    if (presenceNameTag) {
        if (activity.name) {
            presenceNameTag.innerHTML = "";
            const a = document.createElement("a");
            a.href = activity.url || "#";
            a.target = "_blank";
            a.textContent = activity.name;
            presenceNameTag.appendChild(a);
        } else {
            presenceNameTag.style.display = "none";
        }
    }

    // Presence details
    const presenceDetailsTag = document.getElementById("PRESENCE_DETAILS");
    if (presenceDetailsTag) {
        if (activity.details) {
            presenceDetailsTag.textContent = activity.details.length > 25 ? activity.details.slice(0, 25) + "..." : activity.details;
            presenceDetailsTag.style.display = "block";
        } else {
            presenceDetailsTag.style.display = "none";
        }
    }

    // Presence state
    const presenceStateTag = document.getElementById("PRESENCE_STATE");
    if (presenceStateTag) {
        if (activity.state) {
            presenceStateTag.textContent = activity.state.length > 25 ? activity.state.slice(0, 25) + "..." : activity.state;
            presenceStateTag.style.display = "block";
        } else {
            presenceStateTag.style.display = "none";
        }
    }

    // Start and End time
    const startTimeTag = document.getElementById("START_TIME");
    const endTimeTag = document.getElementById("END_TIME");
    if (startTimeTag) startTimeTag.textContent = String(activity.timestamps?.start || "");
    if (endTimeTag) endTimeTag.textContent = String(activity.timestamps?.end || "");

    // atomicradio special
    if (activity.name === "atomicradio") {
        const song_id = (activity.assets.large_image_url || "").split("/").pop().split(".")[0];
        const preview_url = `https://assets.atomic.radio/tracks/previews/${song_id}.aac`;

        const audioPlayer = document.getElementById("audioPlayer");
        if (audioPlayer) {
            fetch(preview_url, { method: "HEAD" })
                .then(response => {
                    if (response.ok) {
                        audioPlayer.src = preview_url;
                    } else {
                        audioPlayer.src = `https://listen.atomic.radio/${activity.assets.small_image_text.toLowerCase()}/lowquality`;
                    }
                })
                .catch(() => {
                    audioPlayer.src = `https://listen.atomic.radio/${activity.assets.small_image_text.toLowerCase()}/lowquality`;
                });

            if (banner) {
                const preview_gif_url = `https://assets.atomic.radio/tracks/previews/${song_id}.mp4`;
                fetch(preview_gif_url, { method: "HEAD" })
                    .then(response => {
                        if (response.ok) {
                            banner.remove();
                            const video = document.createElement("video");
                            video.autoplay = true;
                            video.loop = true;
                            video.muted = true;
                            video.id = "bgimage";
                            video.className = "bgimage";
                            video.src = preview_gif_url;
                            video.style.filter = "blur(5px) brightness(0.5)";
                            const profileCard = document.getElementById("profile-card");
                            if (profileCard) profileCard.insertBefore(video, profileCard.firstChild);
                        }
                    }).catch(() => {
                        banner.src = presence.banner;
                    });
            }

            const presenceName = document.getElementById("PRESENCE_NAME");
            if (presenceName) {
                presenceName.innerHTML = "";
                const a = document.createElement("a");
                a.href = `https://atomic.radio/${activity.assets.small_image_text.toLowerCase()}`;
                a.style = "color: #a9f923; text-decoration: none;";
                a.textContent = "atomicradio";
                presenceName.appendChild(a);
            }

            initializePlaybar();
        }
    }
}
