# LIBRARY
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
# END LIBRARY


############################ L I N K E D I N ############################
# Function for Open Chrome and Login to LinkedIN
def open_chrome():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Buka browser dalam mode layar penuh

    driver = webdriver.Chrome(options=chrome_options)

    # Buka LinkedIn
    driver.get("https://www.linkedin.com/login")

    # Tunggu beberapa detik untuk memastikan halaman terbuka
    time.sleep(3)

    email_input = driver.find_element(By.XPATH, "//input[@aria-label='Email or phone']")
    email_input.send_keys("username")

    password_input = driver.find_element(By.XPATH, "//input[@id='password']")
    password_input.send_keys("password")

    # Tekan tombol login
    password_input.send_keys(Keys.RETURN)
    return driver
# End Function for Open Chrome and Login to LinkedIN

def import_to_csv(company_names,job_titles,posted_ons,job_details,skills,image_src,type_location,locations,link_job,job):
    df = pd.DataFrame({
        "Company Names":company_names, "Job Titles":job_titles,"Posted On":posted_ons,"Job Details":job_details,"Skill":skills,
        "Images":image_src,"Type Location":type_location,"Locations":locations,"Link":link_job}) 
    df = df.drop_duplicates()
    df.to_csv(job+".csv", index=False) # Nama Ubah Sesuai Search
# END

# Function for Scrapping data job in LinkedIn
def find_jobs(driver) : 
    # jobs = ['Data Science','Data Analyst','Data Engineer','Backend','Frontend','Website','Mobile','IoT','Generative AI','UI UX','Software Engineer','Product Manager']
    jobs = ['Machine Learning']
    
    for job in jobs:
        # Buka LinkedIn
        driver.get("https://www.linkedin.com/jobs/search")

        search_job = driver.find_element(By.XPATH, "//input[@aria-label='Search by title, skill, or company']")
        search_job.clear()
        search_job.send_keys(job, Keys.ENTER)

        company_names,job_titles,posted_ons,job_details,skills,image_src,type_location,locations,link_job = [],[],[],[],[],[],[],[],[] 
        time.sleep(5)
        for z in range(500):
            # Ambil elemen <ul> dengan class "scaffold-layout__list-container"
            ul_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "scaffold-layout__list-container"))
            )

            # Temukan semua elemen <li> di dalam <ul> tersebut
            li_elements = ul_element.find_elements(By.TAG_NAME, "li")

            # Ambil semua nilai atribut "data-occludable-job-id" dari setiap <li>, dan hapus yang None
            job_ids = [li.get_attribute("data-occludable-job-id") for li in li_elements if li.get_attribute("data-occludable-job-id") is not None]

            for i in range(len(job_ids)) :
                try : 
                    job_list = job_ids[i]
                    job_list = driver.find_element(By.XPATH, "//li[@data-occludable-job-id="+job_list+"]")
                    # Cari tag <img> di dalam elemen <li> tersebut
                    img_element = job_list.find_element(By.TAG_NAME, "img")

                    # Dapatkan atribut src dari tag <img>
                    img_element = img_element.get_attribute("src")

                    # Cetak URL dari gambar tersebut
                    image_src.append(img_element)
                    job_list.click()

                    time.sleep(1)
                    get_url_div = driver.find_element(By.XPATH, '''//div[@class="relative
          job-details-jobs-unified-top-card__container--two-pane"]''')
                    get_url = get_url_div.find_element(By.XPATH, '''//div[@class="display-flex justify-space-between flex-wrap mt2"]''')
                    get_url = get_url.find_element(By.TAG_NAME, '''a''')
                    get_url = get_url.get_attribute('href')
                    print("Ini url : ",get_url)
                    link_job.append(get_url)


                    div_tl = get_url_div.find_element(By.XPATH, "//div[@class='mt2 mb2']")
                    div_tl = div_tl.find_elements(By.TAG_NAME, "li")
                    div_tl = ",".join(div_tl[0].text.split(" "))
                    type_location.append(str(div_tl))

                    company_name = driver.find_element(By.XPATH, "//div[@class='job-details-jobs-unified-top-card__company-name']")
                    company_names.append(company_name.text)
                    job_title = driver.find_element(By.XPATH, "//h1[@class='t-24 t-bold inline']")
                    job_titles.append(job_title.text)
                    
                    # Temukan elemen <div> dengan class "t-black--light mt2"
                    div_element = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container")

                    teks = div_element.text
                    teks = teks.split("·")
                    teks_posted = str(teks[1]).strip()
                    teks_location = str(teks[0]).strip()
                    posted_ons.append(teks_posted)
                    locations.append(teks_location)
                    
                    job_detail = driver.find_element(By.XPATH, "//div[@class='job-details-module__content']")
                    job_details.append(job_detail.text)

                    skill = ""
                    skill = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='job-details-how-you-match__skills-item-wrapper display-flex flex-row pt4']"))
                    )

                    skill = WebDriverWait(skill, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//a[@class='app-aware-link  job-details-how-you-match__skills-item-subtitle t-14 overflow-hidden']"))
                    )

                    print("Ini Job Title : ",job_title.text)
                    print("Ini skill : ", skill.text)
                    skills.append(skill.text)

                # Bagian except
                except Exception as e:
                    i -= 1
                    # Menghitung panjang minimum dari list yang ada
                    min_length = min(len(company_names), len(job_titles), len(posted_ons), len(job_details), len(skills))
                    
                    # Menghapus elemen terakhir dari list yang panjangnya lebih dari panjang minimum
                    if len(company_names) > min_length:
                        company_names = company_names[:min_length]
                    if len(job_titles) > min_length:
                        job_titles = job_titles[:min_length]
                    if len(posted_ons) > min_length:
                        posted_ons = posted_ons[:min_length]
                    if len(job_details) > min_length:
                        job_details = job_details[:min_length]
                    if len(skills) > min_length:
                        skills = skills[:min_length]
                    if len(image_src) > min_length:
                        image_src = image_src[:min_length]
                    if len(type_location) > min_length:
                        type_location = type_location[:min_length]
                    if len(locations) > min_length:
                        locations = locations[:min_length]
                    if len(link_job) > min_length:
                        link_job = link_job[:min_length]
                    
                    # Lanjutkan dengan iterasi
                    continue
                time.sleep(1)
            try :
                next = driver.find_element(By.XPATH, "//button[@class='artdeco-button artdeco-button--muted artdeco-button--icon-right artdeco-button--1 artdeco-button--tertiary ember-view jobs-search-pagination__button jobs-search-pagination__button--next']")
                next.click()
            except Exception as e :
                break
            
        # import_to_csv(company_names,job_titles,posted_ons,job_details,skills,job)
        import_to_csv(company_names,job_titles,posted_ons,job_details,skills,image_src,type_location,locations,link_job,job)

# Do It
driver = open_chrome()
find_jobs(driver)
# END
############################ E N D   L I N K E D I N ############################