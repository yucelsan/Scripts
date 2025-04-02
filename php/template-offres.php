<?php

/* Template Name: Offres d'Emploi */
// Crétaion de plugin PHP pour le site YUCELSAN
// Développement sur mesure
// AUTHOR : SERDAR AYSAN
// COMPANY : YUCELSAN SAS
// CODE : PHP / THEME : VAXIMO

get_header();
?>

<div style="padding-top: 140px;"></div> <!-- Ajout d'un espace sous le header -->

<h1>Nos Offres d'Emploi</h1>

<?php
$args = array(
    'post_type' => 'offres_emploi', // Récupère toutes les offres
    'posts_per_page' => 10,
);
$query = new WP_Query($args);

if ($query->have_posts()) :
    while ($query->have_posts()) : $query->the_post(); ?>
        <div class="job-offer">
            <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <p><?php // the_excerpt(); ?></p>
            <a href="<?php the_permalink(); ?>" class="view-details">Voir l'offre</a>
        </div>
    <?php endwhile;
    wp_reset_postdata();
else :
    echo "<p>Aucune offre d'emploi disponible.</p>";
endif;

get_footer();
