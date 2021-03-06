"""
Randy Olson's Shortest Route Program modified By Andrew Liesinger to:
    1: Detect waypoints file at runtime - if found use it, otherwise look up distances via google calls (and then save to waypoint file)
    2: Dynamically create and open an HTML file showing the route when a shorter route is found
    3: Make it easier to tinker with the Generation / Population parameters
"""
from __future__ import print_function
from itertools import combinations
import googlemaps
import pandas as pd
import numpy as np
import os.path
import random
import webbrowser

GOOGLE_MAPS_API_KEY = "API_KEY_HERE"
waypoints_file = "my-waypoints-dist-dur.tsv"

#This is the general filename - as shorter routes are discovered the Population fitness score will be inserted into the filename
#so that interim results are saved for comparision.  The actual filenames using the default below will be:
#Output_<Population Fitness Score>.html 
output_file = 'Output.html'

#parameters for the Genetic algoritim
thisRunGenerations=5000
thisRunPopulation_size=300

start_point = "BMW Welt, Munich, Germany"
end_point = "Grauwallring 2, 27580, Bremerhaven, Germany"
all_waypoints = [start_point,
				
				# Optional
				#"Neuschwanstein Castle, Neuschwansteinstrabe 20, 87645 Schwangau, Germany",
				#"Oberstdorf, Germany",
				#"Crimeo 114, 6563 Mesocco, Switzerland",
				#"Splugenpassstrasse 104, 7435 Splugen, Switzerland",

				# Visit
				"Milan Cathedral, Milan, Metropolitan City of Milan, Italy",
				"Galleria Vittorio Emanuele II, Piazza del Duomo, Milan, Metropolitan City of Milan, Italy",
				"Piazza della Signoria, Florence, Italy",
				"Piazza del Duomo, Florence, Metropolitan City of Florence, Italy",
				"Giardino Bardini, Florence, Metropolitan City of Florence, Italy",
				"Colosseum, Piazza del Colosseo, Rome, Metropolitan City of Rome, Italy",
				"Pantheon, Piazza della Rotonda, Rome, Italy",
				"Roman Forum, Via della Salara Vecchia, Rome, Metropolitan City of Rome, Italy",
				"Palatino. Via di San Gregorio, 00186 Roma, Italy",

				# Drive through
				"Piazza San Pietro, Vatican City",

				# Visit
				"Boccadasse, Genoa, Metropolitan City of Genoa, Italy",
				"Piazza Raffaele De Ferrari, Genoa, Metropolitan City of Genoa, Italy",

				# Drive through
				"Vernazza, Province of La Spezia, Italy",

				# Visit
				"Port Hercule, Monte Carlo, Monaco",
				"Place du Palais, Monaco-Ville, Monaco",
				"Castle Hill, Nice, France",
				"Promenade des Anglais, Nice, France",
				"Mont Boron, Nice, France",

				# Optional
				#"Parc national des Calanques, Marseille, France",
				#"Old Port of Marseille",
				#"Place de la Comedie, Montpellier, France",

				# Visit
				"La Sagrada Familia, Carrer de Mallorca, 401, 08013 Barcelona, Spain",

				# Drive through
				"Placa Sant Eudald, 9, 17500 Ripoll, Girona, Spain",
				"Andorra la Vella, Andorra",

				# Optional
				#"Place du Capitole, Toulouse, France",
				#"Place de la Bourse, Bordeaux, France",

				# Visit
				"Eiffel Tower, Avenue Anatole France, Paris, France",
				"Arc de Triomphe, Place Charles de Gaulle, Paris, France",
				"Palace of Westminster, London, United Kingdom",
				"Grand Place, Brussels, Belgium",
				"Nurburgring, Nurburgring Boulevard, Nuerburg, Germany",

				# Drive through
				"Cathedrale Notre-Dame, Rue Notre Dame, Luxembourg City, Luxembourg",

				# Visit
				"Park Plaza Victoria Amsterdam, Damrak, Amsterdam, Netherlands",
				end_point]

def CreateOptimalRouteHtmlFile(optimal_route, distance, display=True):
    optimal_route = list(optimal_route)
    #optimal_route += [optimal_route[0]]

    Page_1 = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
        <meta name="description" content="Randy Olson uses machine learning to find the optimal road trip across the U.S.">
        <meta name="author" content="Randal S. Olson">
        
        <title>The optimal road trip across the U.S. according to machine learning</title>
        <style>
          html, body, #map-canvas {
            height: 100%;
            margin: 0px;
            padding: 0px
          }
          #panel {
            position: absolute;
            top: 5px;
            left: 50%;
            margin-left: -180px;
            z-index: 5;
            background-color: #fff;
            padding: 10px;
            border: 1px solid #999;
          }
        </style>
        <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true"></script>
        <script>
            var routes_list = [];
            var distance = 0.0;
            var duration = 0.0;
            var markerOptions = {icon: "http://maps.gstatic.com/mapfiles/markers2/marker.png"};
            var directionsDisplayOptions = {preserveViewport: true,
            								durationInTraffic : true,
                                            markerOptions: markerOptions};
            var directionsService = new google.maps.DirectionsService();
            var map;

            function initialize() {
              var center = new google.maps.LatLng(53, 9);
              var mapOptions = {
                zoom: 5,
                center: center
              };
              map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
              for (i=0; i<routes_list.length; i++) {
                routes_list[i].setMap(map); 
              }
            }

            function calcRoute(start, end, routes) {
              
              var directionsDisplay = new google.maps.DirectionsRenderer(directionsDisplayOptions);

              var waypts = [];
              for (var i = 0; i < routes.length; i++) {
                waypts.push({
                  location:routes[i],
                  stopover:true});
                }
              
              var request = {
                  origin: start,
                  destination: end,
                  waypoints: waypts,
                  optimizeWaypoints: false,
                  travelMode: google.maps.TravelMode.DRIVING,
                  durationInTraffic : true
              };

              directionsService.route(request, function(response, status) {
                if (status == google.maps.DirectionsStatus.OK) {
                    directionsDisplay.setDirections(response);

                    // Total up the distance and duration of each leg.
                    var legs = response.routes[0].legs;
                    for(var i=0; i<legs.length; ++i) {
                      distance += legs[i].distance.value;
                      duration += legs[i].duration.value;
                    }
                    document.getElementById('distance').innerHTML = " Distance: " + (distance*0.000621371) + " miles";
                    document.getElementById('duration').innerHTML = "Duration: " + (duration/60/60/24) + " days";    
                }
              });

              routes_list.push(directionsDisplay);
            }

            function createRoutes(route) {
                // Google's free map API is limited to 10 waypoints so need to break into batches
                //route.push(route[0]);
                var subset = 0;
                while (subset < route.length) {
                    var waypointSubset = route.slice(subset, subset + 10);

                    var startPoint = waypointSubset[0];
                    var midPoints = waypointSubset.slice(1, waypointSubset.length - 1);
                    var endPoint = waypointSubset[waypointSubset.length - 1];

                    calcRoute(startPoint, endPoint, midPoints);

                    subset += 9;
                }
            }
    """
    Page_2 = """
            
            createRoutes(optimal_route);

            google.maps.event.addDomListener(window, 'load', initialize);

        </script>
      </head>
      <body>
        <div id="map-canvas" style="width: 100%; height: 90%;"></div>
        <div id="duration">Duration: </div> 
        <div id="distance">Distance: </div>
      </body>
    </html>
    """

    localoutput_file = output_file.replace('.html', '_' + str(distance) + '.html')
    with open(localoutput_file, 'w') as fs:
        fs.write(Page_1)
        fs.write("\t\t\toptimal_route = {0}".format(str(optimal_route)))
        fs.write(Page_2)

    if display:
        webbrowser.open_new_tab(localoutput_file)


def compute_fitness(solution):
    """
        This function returns the total distance traveled on the current road trip.
        
        The genetic algorithm will favor road trips that have shorter
        total distances traveled.
    """
    
    solution_fitness = 0.0
    
    for index in range(len(solution)):
        waypoint1 = solution[index - 1]
        waypoint2 = solution[index]
        solution_fitness += waypoint_distances[frozenset([waypoint1, waypoint2])]
        
    return solution_fitness

def generate_random_agent():
    """
        Creates a random road trip from the waypoints.
    """
    
    new_random_agent = list(all_waypoints)
    random.shuffle(new_random_agent)
    try:
    	new_random_agent.remove(start_point);
    	new_random_agent.insert(0, start_point);
    except:
    	"Nothing"
    try:
    	new_random_agent.remove(end_point);
    	new_random_agent.append(end_point);
    except:
    	"Nothing"
    return tuple(new_random_agent)

def mutate_agent(agent_genome, max_mutations=3):
    """
        Applies 1 - `max_mutations` point mutations to the given road trip.
        
        A point mutation swaps the order of two waypoints in the road trip.
    """
    
    agent_genome = list(agent_genome)
    num_mutations = random.randint(1, max_mutations)
    
    for mutation in range(num_mutations):
        swap_index1 = random.randint(1, len(agent_genome) - 2)
        swap_index2 = swap_index1

        while swap_index1 == swap_index2:
            swap_index2 = random.randint(1, len(agent_genome) - 2)

        agent_genome[swap_index1], agent_genome[swap_index2] = agent_genome[swap_index2], agent_genome[swap_index1]
            
    return tuple(agent_genome)

def shuffle_mutation(agent_genome):
    """
        Applies a single shuffle mutation to the given road trip.
        
        A shuffle mutation takes a random sub-section of the road trip
        and moves it to another location in the road trip.
    """
    
    agent_genome = list(agent_genome)
    
    start_index = random.randint(1, len(agent_genome) - 2)
    length = random.randint(2, 20)
    
    genome_subset = agent_genome[start_index:start_index + length]
    agent_genome = agent_genome[:start_index] + agent_genome[start_index + length:]
    
    insert_index = random.randint(1, len(agent_genome) + len(genome_subset) - 2)
    agent_genome = agent_genome[:insert_index] + genome_subset + agent_genome[insert_index:]
    
    agent_genome.remove(end_point)
    agent_genome.append(end_point)

    return tuple(agent_genome)

def generate_random_population(pop_size):
    """
        Generates a list with `pop_size` number of random road trips.
    """
    
    random_population = []
    for agent in range(pop_size):
        random_population.append(generate_random_agent())
    return random_population
    
def run_genetic_algorithm(generations=5000, population_size=100):
    """
        The core of the Genetic Algorithm.
        
        `generations` and `population_size` must be a multiple of 10.
    """
    
    current_best_distance = -1
    population_subset_size = int(population_size / 10.)
    generations_10pct = int(generations / 10.)
    
    # Create a random population of `population_size` number of solutions.
    population = generate_random_population(population_size)

    # For `generations` number of repetitions...
    for generation in range(generations):
        
        # Compute the fitness of the entire current population
        population_fitness = {}

        for agent_genome in population:
            if agent_genome in population_fitness:
                continue

            population_fitness[agent_genome] = compute_fitness(agent_genome)

        # Take the top 10% shortest road trips and produce offspring each from them
        new_population = []
        for rank, agent_genome in enumerate(sorted(population_fitness,
                                                   key=population_fitness.get)[:population_subset_size]):
            if (generation % generations_10pct == 0 or generation == generations - 1) and rank == 0:
                current_best_genome = agent_genome
                print("Generation %d best: %d | Unique genomes: %d" % (generation,
                                                                       population_fitness[agent_genome],
                                                                       len(population_fitness)))
                print(agent_genome)                
                print("")

                # If this is the first route found, or it is shorter than the best route we know,
                # create a html output and display it
                if population_fitness[agent_genome] < current_best_distance or current_best_distance < 0:
                    current_best_distance = population_fitness[agent_genome]
                    CreateOptimalRouteHtmlFile(agent_genome, current_best_distance, False)
                    

            # Create 1 exact copy of each of the top road trips
            new_population.append(agent_genome)

            # Create 2 offspring with 1-3 point mutations
            for offspring in range(2):
                new_population.append(mutate_agent(agent_genome, 3))
                
            # Create 7 offspring with a single shuffle mutation
            for offspring in range(7):
                new_population.append(shuffle_mutation(agent_genome))

        # Replace the old population with the new population of offspring 
        for i in range(len(population))[::-1]:
            del population[i]

        population = new_population


    # Print travel times
    print("\nEstimated travel time (without/with) traffic:")
    total_travel_time = 0.0
    for index in range(len(current_best_genome)-1):
    	waypoint1 = current_best_genome[index]
    	waypoint2 = current_best_genome[index + 1]
    	travel_time = 0.0
    	travel_time = waypoint_durations[frozenset([waypoint1, waypoint2])]/60.0/60.0
    	total_travel_time += travel_time
    	print("From " + waypoint1 + " to " + waypoint2 + ": " + "{0:.2f}".format(travel_time) + "/" + "{0:.2f}".format(travel_time*1.5) + " hrs")

    print ("Total travel time: " + "{0:.2f}".format(total_travel_time/24) + "/" + "{0:.2f}".format(total_travel_time/24*1.5) + " days")
    return current_best_genome


if __name__ == '__main__':
    # If this file exists, read the data stored in it - if not then collect data by asking google
    print("Begin finding shortest route")
    file_path = waypoints_file
    if os.path.exists(file_path):
        print("Waypoints exist")
        #file exists used saved results
        waypoint_distances = {}
        waypoint_durations = {}
        all_waypoints = set()

        waypoint_data = pd.read_csv(file_path, sep="\t")

        for i, row in waypoint_data.iterrows():
            waypoint_distances[frozenset([row.waypoint1, row.waypoint2])] = row.distance_m
            waypoint_durations[frozenset([row.waypoint1, row.waypoint2])] = row.duration_s
            all_waypoints.update([row.waypoint1, row.waypoint2])

    else:
        # File does not exist - compute results       
        print("Collecting Waypoints")
        waypoint_distances = {}
        waypoint_durations = {}


        gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)
        for (waypoint1, waypoint2) in combinations(all_waypoints, 2):
            try:
            	print("Routing from [" + waypoint1 + "] to [" + waypoint2 + "]");
                route = gmaps.distance_matrix(origins=[waypoint1],
                                              destinations=[waypoint2],
                                              mode="driving", # Change to "walking" for walking directions,
                                                              # "bicycling" for biking directions, etc.
                                              language="English",
                                              units="metric")

                # "distance" is in meters
                distance = route["rows"][0]["elements"][0]["distance"]["value"]

                # "duration" is in seconds
                duration = route["rows"][0]["elements"][0]["duration"]["value"]

                waypoint_distances[frozenset([waypoint1, waypoint2])] = distance
                waypoint_durations[frozenset([waypoint1, waypoint2])] = duration
        
            except Exception as e:
                print("Error with finding the route between %s and %s." % (waypoint1, waypoint2))
        
        print("Saving Waypoints")
        with open(waypoints_file, "w") as out_file:
            out_file.write("\t".join(["waypoint1",
                                      "waypoint2",
                                      "distance_m",
                                      "duration_s"]))
        
            for (waypoint1, waypoint2) in waypoint_distances.keys():
                out_file.write("\n" +
                               "\t".join([waypoint1,
                                          waypoint2,
                                          str(waypoint_distances[frozenset([waypoint1, waypoint2])]),
                                          str(waypoint_durations[frozenset([waypoint1, waypoint2])])]))

    print("Search for optimal route")
    optimal_route = run_genetic_algorithm(generations=thisRunGenerations, population_size=thisRunPopulation_size)

    # This is probably redundant now that the files are created in run_genetic_algorithm,
    # but leaving it active to ensure  the final result is not lost
    CreateOptimalRouteHtmlFile(optimal_route, 1, True)
