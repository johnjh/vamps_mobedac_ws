load 'deploy' if respond_to?(:namespace) # cap2 differentiator

Dir['vendor/gems/*/recipes/*.rb','vendor/plugins/*/recipes/*.rb'].each { |plugin| load(plugin) }

load 'config/deploy' # remove this line to skip loading any of the default tasks

after  'deploy:update_code','config_link:symlink'

namespace :deploy do
  task :start do
#    workling.start
 #   passenger.start rescue nil # This catches the error if we don't have an app server defined
  end

  task :dummy_final_task do
    puts "Got to the dummy final task"
  end

  
  task :restart do
    run "touch #{current_release}/tmp/restart.txt"
  end
  
  task :stop do
  end
end

namespace :config_link do
  desc "Make symlink for ws.ini"
  task :symlink do
    run "ln -nfs #{shared_path}/config/ws.ini #{release_path}/ws.ini"
  end
end
