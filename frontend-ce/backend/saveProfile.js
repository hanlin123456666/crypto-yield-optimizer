const express = require("express");
const fs = require("fs");
const cors = require("cors");
const app = express();
const PORT = 5050;

app.use(cors());
app.use(express.json());

app.post("/save-profile", (req, res) => {
  const profile = req.body;

  // Save the incoming profile to a JSON file
  fs.writeFile(
    "./user_profile.json",
    JSON.stringify(profile, null, 2),
    (err) => {
      if (err) {
        console.error("Error writing to JSON file:", err);
        return res.status(500).send("Error saving profile.");
      }

      console.log("Profile saved:", profile);
      res.send("Profile saved successfully.");
    }
  );
});

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
});
