# Install required packages for the Health Centers Shiny Application
# Run this script first before running app.R

# List of required packages
packages <- c(
  "shiny",
  "shinydashboard", 
  "DT",
  "leaflet",
  "plotly",
  "dplyr",
  "readr",
  "readxl",
  "shinycssloaders",
  "shinyWidgets",
  "ggplot2"
)

# Function to install packages if they're not already installed
install_if_missing <- function(package_name) {
  if (!require(package_name, character.only = TRUE)) {
    install.packages(package_name, dependencies = TRUE)
    library(package_name, character.only = TRUE)
  }
}

# Install all required packages
cat("Installing required packages for Health Centers Surveillance System...\n")

for (package in packages) {
  cat(paste("Checking/Installing:", package, "\n"))
  install_if_missing(package)
}

cat("\n✓ All packages installed successfully!\n")
cat("You can now run the application with: shiny::runApp('app.R')\n")