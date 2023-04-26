# Mirrulations

Software to create and maintain a mirror of regulations.gov.

## Architecture
The image below shows the overview of the architecture for our system. It shows the relationship between components and how they are used in the system.
![Architecture](architecture.png)
#### Regulations.gov
------
The data on [Regulations.gov](https://www.regulations.gov) consists of Congressional laws that have been passed and implemented as regulations by federal agencies. The site is available to the public such that anyone can read and provide feedback for these regulations to make their opinions known.


#### The Problem
------

The way that Regulations.gov is currently set up, users may search for and comment on regulations on the main site. However, finding older regulations through the site's API has become a more difficult and limited process where users must apply for an API key to be granted time-limited access to larger sets of data.


The reason users must apply for an API key is because Regulations.gov has taken steps toward conserving their system resources by limiting how many times per hour a user can query the API. This came about after late-show host, John Oliver, called attention to the [fight for net neutrality](https://www.cbsnews.com/news/john-oliver-fans-flood-fcc-website-in-fight-for-net-neutrality/) in 2017 where a flood of viewers crashed the FCC's website with their comments. In an effort to reduce the overall traffic, API access is now limited to one account per organization as well and requires an approval process to validate API keys.

#### The Objective
------

The objective of the Mirrulations project is to make the data on Regulations.gov more easily accessible to the public by acting as a mirror to the site. Since it is federal data, it must be available (with exceptions) to the public under the [Freedom of Information Act](https://foia.state.gov/Learn/FOIA.aspx). By making the data readily available in one place, analysts can more easily study it.

#### The Solution
------
The Mirrulations project endeavors to create a mirror of the regulatory data on Regulations.gov to make it more accessible to the general public. Our goal is to collect all of the data from the site and store it in a database/cloud for users to search for at their leisure. The only problem with that is that there are currently over 9.6 million regulations documents (and counting!) to be downloaded.

With the API limiting that is in place, it would take us months to download all of the data by ourselves, so we are creating a volunteer computing system that allows other people to contribute to the expedition of the downloading process. Through this project users can apply for an API key and volunteer their computer's CPU for downloading data and sending it to our server. If you choose to volunteer, the instructions below will help you to help us get up and running.


## Getting Started

If you are interested in becoming a developer, see `docs/developers.md`.

To run Mirrulations, you need Python 3.9 or greater ([MacOSX](https://docs.python-guide.org/starting/install3/osx/) or [Windows](https://docs.python-guide.org/starting/install3/win/)) on your machine to run this, as well as [redis](https://redis.io/) if you are running a server

You will also need a valid API key from Regulations.gov to participate. To apply for a key, you must simply [contact the Regulations Help Desk](regulations@erulemakinghelpdesk.com) and provide your name, email address, organization, and intended use of the API. If you are not with any organizations, just say so in your message. They will email you with a key once they've verified you and activated the key.

To download the actual project, you will need to go to our [GitHub page](https://github.com/MoravianUniversity/mirrulations) and [clone](https://help.github.com/articles/cloning-a-repository/) the project to your computer.



### Disclaimers
--------
"Regulations.gov and the Federal government cannot verify and are not responsible for the accuracy or authenticity of the data or analyses derived from the data after the data has been retrieved from Regulations.gov."

In other words, "once the data has been downloaded from Regulations.gov, the U.S. Government cannot verify and is not responsible for the quality, accuracy, reliability, or timeliness of any analyses conducted using the downloaded data."

This product uses the Regulations.gov Data API but is neither endorsed nor certified by Regulations.gov.

--------
This project is currently being developed by a student research team at Moravian University

## Contributors

#### 2023
* Alexander Flores-Sosa (floressosaa@moravian.edu)
* Bryan Cohen (cohenb@moravian.edu)
* Edgar Perez (pereze03@moravian.edu)
* Edwin Cojitambo (cojitamboe@moravian.edu)
* Evan Toyberg (toyberge@moravian.edu)
* Jack Wagner (wagnerj05@moravian.edu)
* Justin Szaro (szaroj@moravian.edu)
* Kyle Smilon (smilonk@moravian.edu)
* Nikolas Kovacs (kovacsn@moravian.edu)
* Reed Sturza (sturzar@moravian.edu)
* Tanishq Iyer (iyert@moravian.edu)
* Tyler Valentine (valentinet02@moravian.edu)


#### 2022

* Abdullah Alramyan (abdullaha@moravian.edu)
* Valeria Aguilar (aguilarv@moravian.edu)
* Jack Fineanganofo (fineanganofoj@moravian.edu)
* Richard Glennon (glennonr@moravian.edu)
* Eric Gorski (gorskie@moravian.edu)
* Shane Houghton (houghtons@moravian.edu)
* Benjamin Jones (jonesb04@moravian.edu)
* Matthew Kosack (koasckm@moravian.edu)
* Cory Little (littlec@moravian.edu)
* Michael Marchese (marchesem@moravian.edu)
* Kimberly Miller (millerk10@moravian.edu)
* Mark Morykan (morykanm@moravian.edu)
* Robert Rabinovich (rabinovichr@moravian.edu)
* Maxwell Schuman (schumanm@moravian.edu)
* Elizabeth Vincente (vincentee@moravian.edu)
* Kimberly Wolf (wolfk@moravian.edu)
* Isaac Wood (woodi@moravian.edu)

#### 2021

* Abdullah Alharbi (alharbia02@moravian.edu)
* Alex Meci (mecia@moravian.edu)
* Colby Hillman (hillmanc@moravian.edu)
* Emily Heiser (heisere@moravian.edu)
* Francis Severino-Guzman (severinoguzmanf@moravian.edu)
* Jarod Frekot (frekotj@moravian.edu)
* John Lapatchak (lapatchakjrj@moravian.edu)
* Jonah Beers (beersj02@moravian.edu)
* Jorge Aguilar (aguilarj@moravian.edu)
* Juan Giraldo (giraldoj@moravian.edu)
* Kylie Norwood (norwoodk@moravian.edu)
* Larisa Fava (faval@moravian.edu)
* Riley Kirkpatrick (kirkpatrickr@moravian.edu)
* Trae Freeman (freemant02@moravian.edu)
* William Brandes (brandesw@moravian.edu)

#### 2020

* Alghamdi Riyad (alghamdir@moravian.edu)
* Anderson Ben (andersonb03@moravian.edu)
* Dahdoh Sara (stsad05@moravian.edu)
* Estephan Anthony (estephana02@moravian.edu)
* Faux Timothy (fauxt@moravian.edu)
* Hilal Abrar (stanh17@moravian.edu)
* Ives Elijah (ivese@moravian.edu)
* McCool Caelin (mccoolc@moravian.edu)
* Piya Nischal (piyan@moravian.edu)
* Rajhi Somaya (stsar04@moravian.edu)
* Schmall Kiersten (schmallk@moravian.edu)
* Wang Yuwen (wang@moravian.edu)

#### 2019

* Balga Zachary (stzlb01@moravian.edu) 
* Edwards Manasseh (stmde03@moravian.edu)
* Harbison Ed (stewh01@moravian.edu)
* Haug Alex (stahh02@moravian.edu)
* Mateo Lauren (stlem04@moravian.edu)
* Murphy Timothy (sttam09@moravian.edu)
* Spirk John (stjfs03@moravian.edu)
* Stocker Daniel (stdrs02@moravian.edu)

## Faculty
* Ben Coleman (colemanb@moravian.edu)
