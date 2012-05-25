load 'deploy' if respond_to?(:namespace) # cap2 differentiator

Dir['vendor/gems/*/recipes/*.rb','vendor/plugins/*/recipes/*.rb'].each { |plugin| load(plugin) }

load 'config/deploy' # remove this line to skip loading any of the default tasks

# after a standard deploy:update is run the config_link:symlink and upload_data_link:symlink tasks are run
after  'deploy:update_code', 'fixup_git_files:set_group_permissions', 'config_link:symlink', 'upload_data_link:symlink'

namespace :deploy do
  task :start do
#    workling.start
 #   passenger.start rescue nil # This catches the error if we don't have an app server defined
  end

  task :dummy_final_task do
    puts "Got to the dummy final task"
  end

  # doesn't work for python...only Ruby on Rails app...don't really need this here
  task :restart do
    run "touch #{current_release}/tmp/restart.txt"
  end
  
  task :stop do
  end
end

# makes a symlink for ws.ini so it can really reside in shared/...
namespace :config_link do
  desc "Make symlink for ws.ini"
  task :symlink do
    run "ln -nfs #{shared_path}/config/ws.ini #{release_path}/ws.ini"
  end
end

namespace :upload_data_link do
  desc "Make symlink for upload_data directory"
  task :symlink do
    run "ln -nfs #{shared_path}/upload_data #{release_path}/upload_data"
  end
end

namespace :fixup_git_files do
  desc "Set the group permssions on all files to group writable"
  task :set_group_permissions do
    run "chmod -R g+w #{deploy_to}/shared/cached-copy/*"
  end
end

namespace :server_maint do
  desc "stop the mobedac service"
  task :stop do
    run "curl http://localhost:8080/stop_the_server"
  end
end
