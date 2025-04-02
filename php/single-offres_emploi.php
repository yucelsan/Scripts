<?php

// Crétaion de plugin PHP pour le site YUCELSAN
// Développement sur mesure
// AUTHOR : SERDAR AYSAN
// COMPANY : YUCELSAN SAS
// CODE : PHP / THEME : VAXIMO

get_header(); 
?>

<div style="padding-top: 140px;"></div> <!-- Ajout d'un espace sous le header -->

<div class="single-job-offer">

    <h1><?php the_title(); ?></h1>
    <div class="job-description">
        <?php the_content(); ?>
    </div>

    <!-- Bouton "Postuler" -->
    <button id="postuler-btn">Postuler</button>

    <!-- Formulaire de candidature caché -->
    <div id="job-apply-form" style="display: none;">
        <h2>Postuler pour <span id="job-title"><?php the_title(); ?></span></h2>
        <?php echo do_shortcode('[yucelsan_candidat_form]'); ?>
        <input type="hidden" id="job-id" name="job_id" value="<?php echo get_the_ID(); ?>">
        <input type="hidden" id="job-title-field" name="job_title" value="<?php the_title(); ?>">
    </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("postuler-btn").addEventListener("click", function() {
        let jobTitle = "<?php echo esc_js(htmlspecialchars(get_the_title(), ENT_QUOTES)); ?>"; 
        let jobId = "<?php echo esc_js(get_the_ID()); ?>"; 

        console.log("Titre de l'offre récupéré:", jobTitle); // Vérifie dans la console navigateur (F12)
        
        document.getElementById("job-title").value = jobTitle;
        document.getElementById("job-id").value = jobId;
        document.getElementById("job-apply-form").style.display = "block";
    });
});
</script>

<?php 
get_footer();
